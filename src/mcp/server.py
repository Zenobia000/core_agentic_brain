"""
RAG Knowledge Base MCP Server (FastMCP 版本)
讓 OpenCode 可以透過 MCP 協議呼叫 RAG 功能
"""

import os
import sys
import logging
from pathlib import Path

# 加入專案路徑
BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))

from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RAG_MCP_Server")

# 建立 FastMCP Server
mcp = FastMCP("rag-knowledge-base")

# 延遲初始化 RAG 組件
_retriever = None
_generator = None

def get_retriever():
    global _retriever
    if _retriever is None:
        from src.retrieval.search import HybridRetriever
        _retriever = HybridRetriever()
        logger.info("✅ Retriever 初始化完成")
    return _retriever

def get_generator():
    global _generator
    if _generator is None:
        from src.retrieval.generation import RAGGenerator
        _generator = RAGGenerator()
        logger.info("✅ Generator 初始化完成")
    return _generator


@mcp.tool()
def rag_search(query: str, top_k: int = 5) -> str:
    """搜尋知識庫中的相關資訊。
    
    Args:
        query: 要搜尋的問題或關鍵詞
        top_k: 返回的結果數量，預設 5
    
    Returns:
        相關文件片段、來源頁碼、相關度分數
    """
    if not query:
        return "錯誤：請提供搜尋查詢"
    
    retriever = get_retriever()
    results = retriever.search(query, top_k=top_k)
    
    if not results:
        return "未找到相關結果"
    
    output = f"## 搜尋結果：「{query}」\n\n"
    output += f"找到 {len(results)} 筆相關資料：\n\n"
    
    for i, hit in enumerate(results, 1):
        payload = hit.payload
        output += f"### 結果 {i}\n"
        output += f"- **檔案**: {payload.get('file_name', 'unknown')}\n"
        output += f"- **頁碼**: {payload.get('page_label', '?')}\n"
        output += f"- **相關度**: {hit.score:.2%}\n"
        output += f"- **內容**:\n```\n{payload.get('text', '')[:500]}...\n```\n\n"
    
    return output


@mcp.tool()
def rag_ask(question: str, top_k: int = 5) -> str:
    """根據知識庫內容回答問題，會自動搜尋相關資料並生成回答。
    
    Args:
        question: 要回答的問題
        top_k: 搜尋的文件片段數量，預設 5
    
    Returns:
        AI 生成的回答 + 引用來源
    """
    if not question:
        return "錯誤：請提供問題"
    
    retriever = get_retriever()
    generator = get_generator()
    
    results = retriever.search(question, top_k=top_k)
    
    if not results:
        return "知識庫中沒有找到相關資訊，無法回答此問題。"
    
    answer = generator.generate(question, results)
    
    output = f"## 問題\n{question}\n\n"
    output += f"## 回答\n{answer}\n\n"
    output += f"## 參考來源\n"
    
    for i, hit in enumerate(results, 1):
        payload = hit.payload
        output += f"{i}. **{payload.get('file_name', 'unknown')}** (頁 {payload.get('page_label', '?')}) - 相關度 {hit.score:.2%}\n"
    
    return output


@mcp.tool()
def rag_upload(file_path: str) -> str:
    """上傳 PDF 文件到知識庫。
    
    Args:
        file_path: PDF 檔案的完整路徑
    
    Returns:
        處理狀態
    """
    if not file_path:
        return "錯誤：請提供檔案路徑"
    
    if not os.path.exists(file_path):
        return f"錯誤：檔案不存在 - {file_path}"
    
    if not file_path.lower().endswith('.pdf'):
        return "錯誤：只支援 PDF 檔案"
    
    try:
        from src.ingestion.pipeline import run_ingestion
        run_ingestion(file_path)
        return f"✅ 文件上傳並處理完成：{os.path.basename(file_path)}"
    except Exception as e:
        return f"處理失敗：{str(e)}"


@mcp.tool()
def rag_list_documents() -> str:
    """列出知識庫中的所有文件。
    
    Returns:
        文件列表
    """
    from qdrant_client import QdrantClient
    
    client = QdrantClient(url="http://localhost:6333")
    
    try:
        results = client.scroll(
            collection_name="rag_knowledge_base",
            limit=1000,
            with_payload=True
        )
        
        files = {}
        for point in results[0]:
            file_name = point.payload.get('file_name', 'unknown')
            if file_name not in files:
                files[file_name] = {'count': 0, 'pages': set()}
            files[file_name]['count'] += 1
            files[file_name]['pages'].add(point.payload.get('page_label', '?'))
        
        if not files:
            return "知識庫目前沒有任何文件"
        
        output = "## 知識庫文件列表\n\n"
        for file_name, info in files.items():
            pages = sorted([p for p in info['pages'] if p != '?'], key=lambda x: int(x) if x.isdigit() else 0)
            output += f"- **{file_name}**\n"
            output += f"  - 片段數: {info['count']}\n"
            output += f"  - 頁數: {len(pages)} 頁\n\n"
        
        return output
    except Exception as e:
        return f"錯誤：{str(e)}"


@mcp.tool()
def rag_get_stats() -> str:
    """獲取知識庫的統計資訊。
    
    Returns:
        文件數量、向量數量等統計資訊
    """
    from qdrant_client import QdrantClient
    
    client = QdrantClient(url="http://localhost:6333")
    
    try:
        collection_info = client.get_collection("rag_knowledge_base")
        
        output = "## 知識庫統計\n\n"
        output += f"- **向量數量**: {collection_info.points_count}\n"
        output += f"- **向量維度**: {collection_info.config.params.vectors.size}\n"
        output += f"- **距離函數**: {collection_info.config.params.vectors.distance}\n"
        output += f"- **狀態**: {collection_info.status}\n"
        
        return output
    except Exception as e:
        return f"錯誤：{str(e)}"


if __name__ == "__main__":
    mcp.run()
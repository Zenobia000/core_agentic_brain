"""
RAG MCP Server - FastMCP 版本
提供 RAG 知識庫工具給 OpenCode 使用

啟動方式:
    python -m src.mcp.server

測試方式:
    mcp dev src/mcp/server.py
"""

import os
import sys
import asyncio
import httpx
from pathlib import Path
from typing import Optional

# 確保可以 import 專案模組
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from mcp.server.fastmcp import FastMCP

# 建立 MCP Server
mcp = FastMCP("rag-server")

# RAG API 設定
RAG_API_BASE = os.getenv("RAG_API_BASE", "http://localhost:8001")
TIMEOUT = 120.0  # 上傳大檔案需要較長時間


@mcp.tool()
async def rag_search(query: str, top_k: int = 5) -> str:
    """
    在知識庫中進行語意搜尋
    
    Args:
        query: 搜尋關鍵字或問題
        top_k: 返回結果數量 (預設 5)
    
    Returns:
        搜尋結果列表，包含相關文件片段
    """
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            response = await client.post(
                f"{RAG_API_BASE}/search",
                json={"query": query, "top_k": top_k}
            )
            response.raise_for_status()
            results = response.json()
            
            if not results:
                return "沒有找到相關結果"
            
            # 格式化輸出
            output = []
            for i, r in enumerate(results, 1):
                output.append(f"[{i}] 來源: {r.get('source', 'unknown')} (頁 {r.get('page', '?')})")
                output.append(f"    相關度: {r.get('score', 0):.3f}")
                output.append(f"    內容: {r.get('text', '')[:300]}...")
                output.append("")
            
            return "\n".join(output)
            
        except httpx.HTTPError as e:
            return f"搜尋失敗: {str(e)}"


@mcp.tool()
async def rag_ask(question: str, top_k: int = 5) -> str:
    """
    向知識庫提問並獲得 AI 生成的回答
    
    Args:
        question: 要問的問題
        top_k: 參考的文件數量 (預設 5)
    
    Returns:
        AI 生成的回答，附帶引用來源
    """
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            response = await client.post(
                f"{RAG_API_BASE}/ask",
                json={"question": question, "top_k": top_k}
            )
            response.raise_for_status()
            result = response.json()
            
            answer = result.get("answer", "無法生成回答")
            sources = result.get("sources", [])
            
            output = [answer, "", "📚 參考來源:"]
            for s in sources:
                output.append(f"  - {s.get('source', 'unknown')} (頁 {s.get('page', '?')})")
            
            return "\n".join(output)
            
        except httpx.HTTPError as e:
            return f"提問失敗: {str(e)}"


@mcp.tool()
async def rag_upload(file_path: str) -> str:
    """
    上傳單一 PDF 到知識庫進行索引
    
    Args:
        file_path: PDF 檔案路徑
    
    Returns:
        上傳結果狀態
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        return f"檔案不存在: {file_path}"
    
    if not file_path.suffix.lower() == ".pdf":
        return "只支援 PDF 檔案"
    
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            with open(file_path, "rb") as f:
                files = {"file": (file_path.name, f, "application/pdf")}
                response = await client.post(
                    f"{RAG_API_BASE}/upload",
                    files=files
                )
            response.raise_for_status()
            result = response.json()
            return f"✅ 上傳成功: {result.get('message', file_path.name)}"
            
        except httpx.HTTPError as e:
            return f"上傳失敗: {str(e)}"


@mcp.tool()
async def rag_upload_batch(file_paths: list[str], delay_seconds: float = 2.0) -> str:
    """
    批次上傳多個 PDF 到知識庫
    
    Args:
        file_paths: PDF 檔案路徑列表
        delay_seconds: 每個檔案上傳間隔秒數 (預設 2 秒，避免過載)
    
    Returns:
        批次上傳結果摘要
    """
    results = []
    success_count = 0
    fail_count = 0
    
    for i, file_path in enumerate(file_paths, 1):
        path = Path(file_path)
        
        if not path.exists():
            results.append(f"❌ [{i}/{len(file_paths)}] {path.name}: 檔案不存在")
            fail_count += 1
            continue
        
        if not path.suffix.lower() == ".pdf":
            results.append(f"❌ [{i}/{len(file_paths)}] {path.name}: 不是 PDF 檔案")
            fail_count += 1
            continue
        
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            try:
                with open(path, "rb") as f:
                    files = {"file": (path.name, f, "application/pdf")}
                    response = await client.post(
                        f"{RAG_API_BASE}/upload",
                        files=files
                    )
                response.raise_for_status()
                results.append(f"✅ [{i}/{len(file_paths)}] {path.name}: 上傳成功")
                success_count += 1
                
            except httpx.HTTPError as e:
                results.append(f"❌ [{i}/{len(file_paths)}] {path.name}: {str(e)}")
                fail_count += 1
        
        # 間隔等待，避免過載
        if i < len(file_paths):
            await asyncio.sleep(delay_seconds)
    
    # 總結
    summary = [
        "=" * 40,
        f"📊 批次上傳完成",
        f"   成功: {success_count} 個",
        f"   失敗: {fail_count} 個",
        "=" * 40,
        ""
    ]
    
    return "\n".join(summary + results)


@mcp.tool()
async def rag_upload_directory(directory: str, pattern: str = "*.pdf") -> str:
    """
    上傳目錄中所有符合條件的 PDF 檔案
    
    Args:
        directory: 目錄路徑
        pattern: 檔案匹配模式 (預設 *.pdf)
    
    Returns:
        批次上傳結果摘要
    """
    dir_path = Path(directory)
    
    if not dir_path.exists():
        return f"目錄不存在: {directory}"
    
    if not dir_path.is_dir():
        return f"不是目錄: {directory}"
    
    # 找出所有 PDF 檔案
    pdf_files = list(dir_path.glob(pattern))
    
    if not pdf_files:
        return f"目錄中沒有找到符合 '{pattern}' 的檔案"
    
    # 呼叫批次上傳
    file_paths = [str(f) for f in pdf_files]
    return await rag_upload_batch(file_paths)


@mcp.tool()
async def rag_list_documents() -> str:
    """
    列出知識庫中所有已索引的文件
    
    Returns:
        已索引的文件列表
    """
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            response = await client.get(f"{RAG_API_BASE}/documents")
            response.raise_for_status()
            docs = response.json()
            
            if not docs:
                return "知識庫目前沒有任何文件"
            
            output = ["📚 已索引的文件:", ""]
            for i, doc in enumerate(docs, 1):
                name = doc.get("name", "unknown")
                chunks = doc.get("chunks", "?")
                status = doc.get("status", "unknown")
                output.append(f"  {i}. {name}")
                output.append(f"     狀態: {status} | 區塊數: {chunks}")
            
            return "\n".join(output)
            
        except httpx.HTTPError as e:
            return f"取得文件列表失敗: {str(e)}"


@mcp.tool()
async def rag_get_stats() -> str:
    """
    取得知識庫統計資訊
    
    Returns:
        知識庫統計數據
    """
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            response = await client.get(f"{RAG_API_BASE}/stats")
            response.raise_for_status()
            stats = response.json()
            
            output = [
                "📊 知識庫統計",
                "=" * 30,
                f"文件數量: {stats.get('document_count', 0)}",
                f"總區塊數: {stats.get('total_chunks', 0)}",
                f"向量維度: {stats.get('vector_dim', 'N/A')}",
                f"索引大小: {stats.get('index_size', 'N/A')}",
            ]
            
            return "\n".join(output)
            
        except httpx.HTTPError as e:
            return f"取得統計資訊失敗: {str(e)}"


@mcp.tool()
async def rag_delete_document(document_name: str) -> str:
    """
    從知識庫刪除指定文件
    
    Args:
        document_name: 要刪除的文件名稱
    
    Returns:
        刪除結果
    """
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            response = await client.delete(
                f"{RAG_API_BASE}/documents/{document_name}"
            )
            response.raise_for_status()
            return f"✅ 已刪除文件: {document_name}"
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return f"❌ 找不到文件: {document_name}"
            return f"❌ 刪除失敗: {str(e)}"
        except httpx.HTTPError as e:
            return f"❌ 刪除失敗: {str(e)}"


@mcp.tool()
async def rag_get_status(file_name: str) -> str:
    """
    查詢文件的處理狀態
    
    Args:
        file_name: 文件名稱
    
    Returns:
        文件處理狀態
    """
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            response = await client.get(f"{RAG_API_BASE}/status/{file_name}")
            response.raise_for_status()
            status = response.json()
            
            output = [
                f"📄 文件: {file_name}",
                f"狀態: {status.get('status', 'unknown')}",
                f"進度: {status.get('progress', 0)}%",
            ]
            
            if status.get('error'):
                output.append(f"錯誤: {status.get('error')}")
            
            return "\n".join(output)
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return f"找不到文件: {file_name}"
            return f"查詢失敗: {str(e)}"
        except httpx.HTTPError as e:
            return f"查詢失敗: {str(e)}"


# 啟動 Server
if __name__ == "__main__":
    mcp.run()
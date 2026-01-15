"""
RAG MCP Server - FastMCP 版本 v3
提供 RAG 知識庫工具給 OpenCode 使用

更新內容 v3:
- 新增聯網搜尋功能 (DuckDuckGo)
- 新增 rag_ask_with_web 整合問答
- 改進所有 Tool 的描述 (提示詞工程)
- 修正 rag_list_documents 格式處理
- 結果緩存功能

啟動方式:
    python -m src.mcp.server

測試方式:
    mcp dev src/mcp/server.py
"""

import os
import sys
import asyncio
import hashlib
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
from collections import OrderedDict

# 確保可以 import 專案模組
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import httpx
from mcp.server.fastmcp import FastMCP

# 嘗試導入 DuckDuckGo 搜尋
try:
    from duckduckgo_search import DDGS
    SEARCH_AVAILABLE = True
except ImportError:
    SEARCH_AVAILABLE = False
    print("⚠️ duckduckgo_search 未安裝，聯網搜尋功能將不可用")
    print("   安裝指令: pip install duckduckgo_search")

# 建立 MCP Server
mcp = FastMCP("rag-server")

# RAG API 設定
RAG_API_BASE = os.getenv("RAG_API_BASE", "http://localhost:8001")
TIMEOUT = 120.0  # 上傳大檔案需要較長時間

# ============================================================
# 緩存系統
# ============================================================

class LRUCache:
    """簡單的 LRU 緩存，支援過期時間"""
    
    def __init__(self, max_size: int = 100, ttl_seconds: int = 3600):
        self.cache: OrderedDict = OrderedDict()
        self.max_size = max_size
        self.ttl = ttl_seconds
    
    def _make_key(self, *args, **kwargs) -> str:
        """生成緩存 key"""
        key_str = str(args) + str(sorted(kwargs.items()))
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """取得緩存值，如果過期則返回 None"""
        if key not in self.cache:
            return None
        
        value, timestamp = self.cache[key]
        if time.time() - timestamp > self.ttl:
            del self.cache[key]
            return None
        
        # 移到最後 (LRU)
        self.cache.move_to_end(key)
        return value
    
    def set(self, key: str, value: Any):
        """設定緩存值"""
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = (value, time.time())
        
        # 超過大小限制時移除最舊的
        while len(self.cache) > self.max_size:
            self.cache.popitem(last=False)
    
    def clear(self):
        """清空緩存"""
        self.cache.clear()
    
    def stats(self) -> Dict[str, Any]:
        """緩存統計"""
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "ttl_seconds": self.ttl
        }

# 建立緩存實例
search_cache = LRUCache(max_size=100, ttl_seconds=1800)  # 搜尋緩存 30 分鐘
ask_cache = LRUCache(max_size=50, ttl_seconds=3600)      # 問答緩存 1 小時
web_cache = LRUCache(max_size=50, ttl_seconds=600)       # 網路搜尋緩存 10 分鐘

# ============================================================
# MCP Tools - 核心 RAG 功能
# ============================================================

@mcp.tool()
async def rag_search(query: str, top_k: int = 5, use_cache: bool = True) -> str:
    """
    在企業知識庫中進行語意搜尋，找出與問題最相關的文件段落。
    
    這個工具適合用於：
    - 查找技術文件、論文、產品說明中的特定內容
    - 了解某個概念、技術或術語的定義
    - 收集多個相關段落以便進行比較分析
    - 在回答問題前先收集背景資料
    
    使用建議：
    - 使用完整的句子或問題作為 query，效果比關鍵字更好
    - 如果結果不夠精確，嘗試換個方式描述問題
    - top_k 建議設 3-10，太多會包含不相關內容
    
    Args:
        query: 搜尋問題或關鍵字（建議使用完整句子）
        top_k: 返回結果數量，預設 5，範圍 1-20
        use_cache: 是否使用緩存，預設 True
    
    Returns:
        搜尋結果列表，每個結果包含：
        - 來源檔案名稱和頁碼
        - 相關度分數 (0-1，越高越相關)
        - 文件內容片段
    """
    # 檢查緩存
    cache_key = search_cache._make_key(query, top_k)
    if use_cache:
        cached = search_cache.get(cache_key)
        if cached:
            return f"[緩存結果]\n{cached}"
    
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            response = await client.post(
                f"{RAG_API_BASE}/search",
                json={"query": query, "top_k": top_k}
            )
            response.raise_for_status()
            results = response.json()
            
            if not results:
                return "沒有找到相關結果。建議：\n1. 嘗試使用不同的關鍵字\n2. 確認知識庫中是否有相關文件"
            
            # 格式化輸出
            output = [f"🔍 找到 {len(results)} 個相關結果：\n"]
            for i, r in enumerate(results, 1):
                source = r.get('source', 'unknown')
                page = r.get('page', '?')
                score = r.get('score', 0)
                text = r.get('text', '')[:300]
                
                output.append(f"【{i}】{source} (第 {page} 頁)")
                output.append(f"    相關度: {score:.1%}")
                output.append(f"    內容: {text}...")
                output.append("")
            
            result_text = "\n".join(output)
            
            # 存入緩存
            if use_cache:
                search_cache.set(cache_key, result_text)
            
            return result_text
            
        except httpx.HTTPError as e:
            return f"❌ 搜尋失敗: {str(e)}\n請確認 RAG API 服務是否正常運行 (http://localhost:8001)"


@mcp.tool()
async def rag_ask(question: str, top_k: int = 5, use_cache: bool = True) -> str:
    """
    向知識庫提問並獲得 AI 生成的回答，回答會基於知識庫中的實際內容。
    
    這個工具適合用於：
    - 需要綜合多個文件內容來回答的問題
    - 希望得到有引用來源的答案
    - 詢問知識庫中文件的具體內容
    - 比較、總結、分析知識庫中的資訊
    
    與 rag_search 的區別：
    - rag_search: 只返回原始文件片段，需要自己閱讀理解
    - rag_ask: 返回 AI 整理過的答案，並標註引用來源
    
    使用建議：
    - 問題要明確具體，避免太籠統
    - 如果答案不滿意，可以追問或換個角度提問
    
    Args:
        question: 要問的問題（建議使用完整的問句）
        top_k: 參考的文件數量，預設 5
        use_cache: 是否使用緩存，預設 True
    
    Returns:
        AI 生成的回答，包含：
        - 基於知識庫內容的答案
        - 參考來源列表（檔案名稱和頁碼）
    """
    # 檢查緩存
    cache_key = ask_cache._make_key(question, top_k)
    if use_cache:
        cached = ask_cache.get(cache_key)
        if cached:
            return f"[緩存結果]\n{cached}"
    
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
                source = s.get('source', 'unknown')
                page = s.get('page', '?')
                output.append(f"  • {source} (第 {page} 頁)")
            
            result_text = "\n".join(output)
            
            # 存入緩存
            if use_cache:
                ask_cache.set(cache_key, result_text)
            
            return result_text
            
        except httpx.HTTPError as e:
            return f"❌ 提問失敗: {str(e)}\n請確認 RAG API 服務是否正常運行"


# ============================================================
# MCP Tools - 聯網搜尋功能 (新增)
# ============================================================

@mcp.tool()
async def web_search(query: str, max_results: int = 5, use_cache: bool = True) -> str:
    """
    使用 DuckDuckGo 進行網路搜尋，獲取最新的網路資訊。
    
    這個工具適合用於：
    - 查找知識庫中沒有的最新資訊
    - 補充知識庫內容的不足
    - 驗證或更新過時的資訊
    - 搜尋新聞、趨勢、最新發展
    
    與 rag_search 的區別：
    - rag_search: 搜尋本地知識庫（PDF 文件）
    - web_search: 搜尋網際網路（最新資訊）
    
    Args:
        query: 搜尋關鍵字或問題
        max_results: 返回結果數量，預設 5，最多 10
        use_cache: 是否使用緩存，預設 True（緩存 10 分鐘）
    
    Returns:
        網路搜尋結果，包含標題、摘要和連結
    """
    if not SEARCH_AVAILABLE:
        return "❌ 聯網搜尋功能未啟用\n\n請安裝 duckduckgo_search:\npip install duckduckgo_search"
    
    # 限制結果數量
    max_results = min(max_results, 10)
    
    # 檢查緩存
    cache_key = web_cache._make_key(query, max_results)
    if use_cache:
        cached = web_cache.get(cache_key)
        if cached:
            return f"[緩存結果 - 10分鐘內]\n{cached}"
    
    try:
        # 使用 DuckDuckGo 搜尋
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        
        if not results:
            return f"🔍 沒有找到與 '{query}' 相關的網路結果"
        
        # 格式化輸出
        output = [f"🌐 網路搜尋結果 ({len(results)} 筆)：\n"]
        
        for i, r in enumerate(results, 1):
            title = r.get('title', '無標題')
            body = r.get('body', '')[:200]
            href = r.get('href', '')
            
            output.append(f"【{i}】{title}")
            output.append(f"    {body}...")
            output.append(f"    🔗 {href}")
            output.append("")
        
        result_text = "\n".join(output)
        
        # 存入緩存
        if use_cache:
            web_cache.set(cache_key, result_text)
        
        return result_text
        
    except Exception as e:
        return f"❌ 網路搜尋失敗: {str(e)}"


@mcp.tool()
async def web_search_news(query: str, max_results: int = 5) -> str:
    """
    搜尋最新新聞，獲取特定主題的新聞報導。
    
    適合用於：
    - 了解某個主題的最新發展
    - 追蹤產業動態
    - 獲取時事資訊
    
    Args:
        query: 新聞搜尋關鍵字
        max_results: 返回結果數量，預設 5
    
    Returns:
        新聞搜尋結果，包含標題、日期、來源和摘要
    """
    if not SEARCH_AVAILABLE:
        return "❌ 聯網搜尋功能未啟用\n\n請安裝 duckduckgo_search:\npip install duckduckgo_search"
    
    try:
        with DDGS() as ddgs:
            results = list(ddgs.news(query, max_results=max_results))
        
        if not results:
            return f"📰 沒有找到與 '{query}' 相關的新聞"
        
        output = [f"📰 新聞搜尋結果 ({len(results)} 筆)：\n"]
        
        for i, r in enumerate(results, 1):
            title = r.get('title', '無標題')
            body = r.get('body', '')[:150]
            source = r.get('source', '未知來源')
            date = r.get('date', '')
            url = r.get('url', '')
            
            output.append(f"【{i}】{title}")
            output.append(f"    📅 {date} | 📰 {source}")
            output.append(f"    {body}...")
            output.append(f"    🔗 {url}")
            output.append("")
        
        return "\n".join(output)
        
    except Exception as e:
        return f"❌ 新聞搜尋失敗: {str(e)}"


@mcp.tool()
async def rag_ask_with_web(
    question: str, 
    rag_top_k: int = 3, 
    web_results: int = 3
) -> str:
    """
    結合知識庫和網路搜尋的智慧問答，提供更完整的答案。
    
    這個工具會：
    1. 先搜尋本地知識庫（已上傳的 PDF）
    2. 再搜尋網路獲取補充資訊
    3. 整合兩者生成更全面的回答
    
    適合用於：
    - 知識庫資訊可能過時，需要最新資訊補充
    - 問題涉及知識庫以外的內容
    - 需要比較內部文件和外部資訊
    
    與其他工具的區別：
    - rag_ask: 只用知識庫回答
    - web_search: 只搜尋網路
    - rag_ask_with_web: 整合兩者，更完整
    
    Args:
        question: 要問的問題
        rag_top_k: 知識庫搜尋結果數量，預設 3
        web_results: 網路搜尋結果數量，預設 3
    
    Returns:
        整合知識庫和網路資訊的完整回答
    """
    results = []
    
    # 1. 搜尋知識庫
    results.append("📚 **知識庫搜尋結果：**\n")
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(
                f"{RAG_API_BASE}/search",
                json={"query": question, "top_k": rag_top_k}
            )
            response.raise_for_status()
            rag_results = response.json()
            
            if rag_results:
                for i, r in enumerate(rag_results, 1):
                    source = r.get('source', 'unknown')
                    page = r.get('page', '?')
                    text = r.get('text', '')[:200]
                    results.append(f"[{i}] {source} (p.{page}): {text}...")
            else:
                results.append("（知識庫中沒有找到相關內容）")
    except Exception as e:
        results.append(f"（知識庫搜尋失敗: {e}）")
    
    results.append("\n")
    
    # 2. 搜尋網路
    results.append("🌐 **網路搜尋結果：**\n")
    if SEARCH_AVAILABLE:
        try:
            with DDGS() as ddgs:
                web_results_data = list(ddgs.text(question, max_results=web_results))
            
            if web_results_data:
                for i, r in enumerate(web_results_data, 1):
                    title = r.get('title', '')
                    body = r.get('body', '')[:150]
                    results.append(f"[{i}] {title}: {body}...")
            else:
                results.append("（網路上沒有找到相關內容）")
        except Exception as e:
            results.append(f"（網路搜尋失敗: {e}）")
    else:
        results.append("（聯網搜尋功能未啟用）")
    
    results.append("\n")
    
    # 3. 使用 RAG API 生成整合回答
    results.append("💡 **整合回答：**\n")
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(
                f"{RAG_API_BASE}/ask",
                json={"question": question, "top_k": rag_top_k}
            )
            response.raise_for_status()
            answer_data = response.json()
            answer = answer_data.get("answer", "無法生成回答")
            results.append(answer)
    except Exception as e:
        results.append(f"（回答生成失敗: {e}）")
    
    return "\n".join(results)


# ============================================================
# MCP Tools - 文件管理
# ============================================================

@mcp.tool()
async def rag_list_documents() -> str:
    """
    列出知識庫中所有已索引的文件清單。
    
    這個工具適合用於：
    - 了解目前知識庫包含哪些文件
    - 確認某個文件是否已經上傳並索引
    - 在搜尋前先了解知識庫的範圍
    
    Returns:
        已索引的文件列表，包含檔案名稱
    """
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            response = await client.get(f"{RAG_API_BASE}/documents")
            response.raise_for_status()
            docs = response.json()
            
            if not docs:
                return "📭 知識庫目前沒有任何文件。\n\n使用 rag_upload 上傳 PDF 文件來建立知識庫。"
            
            output = [f"📚 知識庫文件清單 (共 {len(docs)} 個)：", ""]
            
            for i, doc in enumerate(docs, 1):
                # 處理字串列表或物件列表
                if isinstance(doc, str):
                    output.append(f"  {i}. 📄 {doc}")
                elif isinstance(doc, dict):
                    name = doc.get("name", doc.get("filename", "unknown"))
                    chunks = doc.get("chunks", "?")
                    status = doc.get("status", "")
                    output.append(f"  {i}. 📄 {name}")
                    if chunks != "?":
                        output.append(f"      區塊數: {chunks}")
                    if status:
                        output.append(f"      狀態: {status}")
                else:
                    output.append(f"  {i}. 📄 {str(doc)}")
            
            return "\n".join(output)
            
        except httpx.HTTPError as e:
            return f"❌ 取得文件列表失敗: {str(e)}"


@mcp.tool()
async def rag_get_stats() -> str:
    """
    取得知識庫的統計資訊，包括文件數量、向量數量等。
    
    這個工具適合用於：
    - 了解知識庫的整體規模
    - 監控知識庫的使用狀況
    - 排查問題時確認系統狀態
    
    Returns:
        知識庫統計數據，包含：
        - 文件數量
        - 總區塊數（向量數量）
        - 向量維度
        - 索引大小
    """
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            response = await client.get(f"{RAG_API_BASE}/stats")
            response.raise_for_status()
            stats = response.json()
            
            output = [
                "📊 知識庫統計資訊",
                "═" * 30,
                f"📁 文件數量: {stats.get('document_count', 0)} 個",
                f"🧩 總區塊數: {stats.get('total_chunks', 0)} 個",
                f"📐 向量維度: {stats.get('vector_dim', 'N/A')}",
                f"💾 索引大小: {stats.get('index_size', 'N/A')}",
                "",
                "📦 緩存狀態:",
                f"   搜尋緩存: {search_cache.stats()['size']}/{search_cache.stats()['max_size']}",
                f"   問答緩存: {ask_cache.stats()['size']}/{ask_cache.stats()['max_size']}",
                f"   網路緩存: {web_cache.stats()['size']}/{web_cache.stats()['max_size']}",
                "",
                f"🌐 聯網搜尋: {'✅ 已啟用' if SEARCH_AVAILABLE else '❌ 未安裝'}",
            ]
            
            return "\n".join(output)
            
        except httpx.HTTPError as e:
            return f"❌ 取得統計資訊失敗: {str(e)}"


@mcp.tool()
async def rag_upload(file_path: str) -> str:
    """
    上傳單一 PDF 文件到知識庫進行索引。
    
    上傳後系統會：
    1. 解析 PDF 內容（使用 IBM Docling）
    2. 將內容切分成小段落
    3. 生成向量並存入 Qdrant
    
    注意事項：
    - 只支援 PDF 格式
    - 大檔案（>10MB）建議先分割
    - 上傳需要一些時間，請耐心等待
    
    Args:
        file_path: PDF 檔案的完整路徑
    
    Returns:
        上傳結果狀態
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        return f"❌ 檔案不存在: {file_path}\n請確認路徑是否正確"
    
    if not file_path.suffix.lower() == ".pdf":
        return f"❌ 只支援 PDF 檔案，目前檔案格式: {file_path.suffix}"
    
    file_size = file_path.stat().st_size / (1024 * 1024)  # MB
    if file_size > 10:
        return f"⚠️ 檔案較大 ({file_size:.1f} MB)，上傳可能需要較長時間..."
    
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
            return f"✅ 上傳成功！\n📄 檔案: {file_path.name}\n💬 {result.get('message', '已加入索引')}"
            
        except httpx.HTTPError as e:
            return f"❌ 上傳失敗: {str(e)}"


@mcp.tool()
async def rag_upload_batch(file_paths: list[str], delay_seconds: float = 2.0) -> str:
    """
    批次上傳多個 PDF 文件到知識庫。
    
    適合用於：
    - 一次上傳多個相關文件
    - 初始化知識庫時批量導入
    
    Args:
        file_paths: PDF 檔案路徑列表
        delay_seconds: 每個檔案上傳間隔秒數，預設 2 秒（避免過載）
    
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
        "═" * 40,
        f"📊 批次上傳完成",
        f"   ✅ 成功: {success_count} 個",
        f"   ❌ 失敗: {fail_count} 個",
        "═" * 40,
        ""
    ]
    
    return "\n".join(summary + results)


@mcp.tool()
async def rag_delete_document(document_name: str) -> str:
    """
    從知識庫刪除指定文件。
    
    注意：刪除後無法恢復，請謹慎操作。
    
    Args:
        document_name: 要刪除的文件名稱（可用 rag_list_documents 查看）
    
    Returns:
        刪除結果
    """
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            response = await client.delete(
                f"{RAG_API_BASE}/documents/{document_name}"
            )
            response.raise_for_status()
            
            # 清空相關緩存
            search_cache.clear()
            ask_cache.clear()
            
            return f"✅ 已刪除文件: {document_name}\n🗑️ 緩存已清空"
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return f"❌ 找不到文件: {document_name}\n請用 rag_list_documents 確認文件名稱"
            return f"❌ 刪除失敗: {str(e)}"
        except httpx.HTTPError as e:
            return f"❌ 刪除失敗: {str(e)}"


@mcp.tool()
async def rag_get_status(file_name: str) -> str:
    """
    查詢文件的處理狀態（上傳後的索引進度）。
    
    Args:
        file_name: 文件名稱
    
    Returns:
        文件處理狀態和進度
    """
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            response = await client.get(f"{RAG_API_BASE}/status/{file_name}")
            response.raise_for_status()
            status = response.json()
            
            status_emoji = {
                "pending": "⏳",
                "processing": "🔄",
                "completed": "✅",
                "failed": "❌"
            }
            
            current_status = status.get('status', 'unknown')
            emoji = status_emoji.get(current_status, "❓")
            
            output = [
                f"📄 文件: {file_name}",
                f"{emoji} 狀態: {current_status}",
                f"📊 進度: {status.get('progress', 0)}%",
            ]
            
            if status.get('error'):
                output.append(f"⚠️ 錯誤: {status.get('error')}")
            
            return "\n".join(output)
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return f"❌ 找不到文件: {file_name}"
            return f"❌ 查詢失敗: {str(e)}"
        except httpx.HTTPError as e:
            return f"❌ 查詢失敗: {str(e)}"


# ============================================================
# MCP Tools - 緩存管理
# ============================================================

@mcp.tool()
async def rag_clear_cache() -> str:
    """
    清空所有緩存（搜尋緩存、問答緩存、網路緩存）。
    
    適合用於：
    - 知識庫內容更新後，需要獲取最新結果
    - 緩存佔用太多記憶體
    - 排查問題時確保獲取即時結果
    
    Returns:
        清空結果
    """
    search_before = search_cache.stats()['size']
    ask_before = ask_cache.stats()['size']
    web_before = web_cache.stats()['size']
    
    search_cache.clear()
    ask_cache.clear()
    web_cache.clear()
    
    return (
        f"🗑️ 緩存已清空\n"
        f"   搜尋緩存: {search_before} → 0\n"
        f"   問答緩存: {ask_before} → 0\n"
        f"   網路緩存: {web_before} → 0"
    )


# ============================================================
# 啟動 Server
# ============================================================

if __name__ == "__main__":
    mcp.run()
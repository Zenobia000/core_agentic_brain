"""
FastAPI 後端 API
提供 REST API 和 WebSocket 接口
"""

import logging
import os
import asyncio
from typing import Optional, List
from contextlib import asynccontextmanager
from pathlib import Path

# 確保載入 .env 檔案（使用專案根目錄）
from dotenv import load_dotenv
_project_root = Path(__file__).resolve().parent.parent
_env_path = _project_root / ".env"
load_dotenv(_env_path)

from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from config.settings import settings
from core.engine import OpenCodeEngine
from core.protocols import Intent, Context, EventType

logging.basicConfig(level=getattr(logging, settings.log_level))
logger = logging.getLogger("API")

# ============== 全域變數 ==============

engine: Optional[OpenCodeEngine] = None


# ============== Lifespan ==============

@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用生命週期管理"""
    global engine
    
    # 啟動
    logger.info("🚀 Starting OpenCode Platform API...")
    
    engine = OpenCodeEngine(config={
        "use_redis": True,
        "redis_url": settings.redis.url
    })
    await engine.initialize()
    
    logger.info("✅ API ready")
    
    yield
    
    # 關閉
    logger.info("Shutting down...")
    if engine:
        await engine.shutdown()


# ============== FastAPI App ==============

app = FastAPI(
    title="OpenCode Platform API",
    description="OpenCode-Centric Intelligent Platform API",
    version=settings.version,
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============== 引入路由 ==============

from api.routes.research import router as research_router
from api.routes.qdrant import router as qdrant_router

app.include_router(research_router)
app.include_router(qdrant_router)


# ============== 全域狀態 ==============

# 文件處理狀態追蹤
processing_status = {}


# ============== Pydantic Models ==============

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"
    selected_docs: Optional[List[str]] = None


class ChatResponse(BaseModel):
    answer: str
    sources: List[dict] = []


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5
    filters: Optional[dict] = None


class AskRequest(BaseModel):
    question: str
    top_k: int = 5


class ExecuteRequest(BaseModel):
    service_id: str
    method: str
    params: dict = {}


class FilteredSearchRequest(BaseModel):
    """篩選搜尋請求"""
    query: str
    filenames: Optional[List[str]] = None
    top_k: int = 5


class StatusResponse(BaseModel):
    """處理狀態回應"""
    status: str
    message: str


# ============== 依賴注入 ==============

async def get_engine() -> OpenCodeEngine:
    """取得引擎實例"""
    if engine is None:
        raise HTTPException(503, "Engine not initialized")
    return engine


# ============== Health Check ==============

@app.get("/health")
async def health_check():
    """健康檢查"""
    return {
        "status": "healthy",
        "engine_ready": engine is not None and engine.is_ready,
        "version": settings.version
    }


# ============== Chat Endpoints ==============

@app.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    eng: OpenCodeEngine = Depends(get_engine)
):
    """同步對話"""
    context = Context(
        session_id=request.session_id,
        user_id="api_user",
        metadata={"selected_docs": request.selected_docs}
    )
    
    intent = Intent.create(
        content=request.message,
        intent_type="chat",
        context=context
    )
    
    answer = ""
    sources = []
    
    async for event in eng.process_intent(intent):
        if event.type == EventType.ANSWER:
            answer = event.payload.get("content", "")
        elif event.type == EventType.SOURCE:
            sources = event.payload.get("data", {}).get("sources", [])
        elif event.type == EventType.ERROR:
            raise HTTPException(500, event.payload.get("content", "Unknown error"))
    
    return ChatResponse(answer=answer, sources=sources)


@app.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    eng: OpenCodeEngine = Depends(get_engine)
):
    """串流對話"""
    logger.info(f"💬 ====== 收到對話請求 ======")
    logger.info(f"💬 訊息: {request.message[:100]}...")
    logger.info(f"💬 選定文件: {request.selected_docs}")
    logger.info(f"💬 Session: {request.session_id}")
    
    context = Context(
        session_id=request.session_id,
        user_id="api_user",
        metadata={"selected_docs": request.selected_docs}
    )
    
    intent = Intent.create(
        content=request.message,
        intent_type="chat",
        context=context
    )
    
    async def event_generator():
        try:
            async for event in eng.process_intent(intent):
                # 正確使用 event.type (不是 event_type)
                event_type_str = event.type.value if hasattr(event.type, 'value') else str(event.type)
                content_preview = str(event.payload.get('content', ''))[:50]
                logger.debug(f"💬 Event: {event_type_str} - {content_preview}...")
                yield event.to_sse()
        except Exception as e:
            logger.error(f"❌ Stream error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            import json
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


# ============== Search Endpoints ==============

@app.post("/search")
async def search(request: SearchRequest):
    """語意搜尋"""
    from services.knowledge_base.service import KnowledgeBaseService
    
    service = KnowledgeBaseService()
    await service.initialize()
    
    result = await service.execute("rag_search", {
        "query": request.query,
        "top_k": request.top_k,
        "filters": request.filters
    })
    
    return result


@app.post("/ask")
async def ask(request: AskRequest):
    """問答"""
    from services.knowledge_base.service import KnowledgeBaseService
    
    service = KnowledgeBaseService()
    await service.initialize()
    
    result = await service.execute("rag_ask", {
        "question": request.question,
        "top_k": request.top_k
    })
    
    return result


@app.post("/search/filtered")
async def filtered_search(request: FilteredSearchRequest):
    """
    在指定的文件中搜尋
    
    - **query**: 搜尋查詢
    - **filenames**: 限定文件列表（可選）
    - **top_k**: 返回結果數量
    """
    try:
        from qdrant_client import QdrantClient
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        from openai import OpenAI
        
        # 確保 .env 已載入
        load_dotenv(_env_path, override=True)
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise HTTPException(500, "OPENAI_API_KEY not configured")
        
        client = QdrantClient(host="localhost", port=6333)
        openai_client = OpenAI(api_key=api_key)
        
        # 生成查詢向量
        embedding_response = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=request.query
        )
        query_vector = embedding_response.data[0].embedding
        
        # 建立篩選條件
        search_filter = None
        if request.filenames and len(request.filenames) > 0:
            if len(request.filenames) == 1:
                search_filter = Filter(
                    must=[FieldCondition(key="file_name", match=MatchValue(value=request.filenames[0]))]
                )
            else:
                search_filter = Filter(
                    should=[
                        FieldCondition(key="file_name", match=MatchValue(value=f))
                        for f in request.filenames
                    ]
                )
        
        # 執行搜尋
        results = client.query_points(
            collection_name="rag_knowledge_base",
            query=query_vector,
            query_filter=search_filter,
            limit=request.top_k,
            with_payload=True
        )
        
        return {
            "results": [
                {
                    "content": point.payload.get("text", ""),
                    "source": point.payload.get("file_name", ""),
                    "page": point.payload.get("page_label", "1"),
                    "score": point.score
                }
                for point in results.points
            ],
            "query": request.query,
            "filtered_by": request.filenames
        }
        
    except Exception as e:
        logger.error(f"Filtered search failed: {e}")
        raise HTTPException(500, f"Search failed: {str(e)}")


# ============== Document Endpoints ==============

@app.get("/documents")
async def list_documents():
    """列出文件"""
    from services.knowledge_base.service import KnowledgeBaseService
    
    service = KnowledgeBaseService()
    await service.initialize()
    
    result = await service.execute("document_list", {})
    return result.get("documents", [])


@app.get("/documents/{name}/content")
async def get_document_content(name: str, limit: int = 100):
    """獲取文件所有內容"""
    try:
        from qdrant_client import QdrantClient
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        
        client = QdrantClient(host="localhost", port=6333)
        
        # 使用 scroll 獲取該文件的所有 chunks
        all_chunks = []
        offset = None
        
        while True:
            results, offset = client.scroll(
                collection_name="rag_knowledge_base",
                scroll_filter=Filter(
                    must=[FieldCondition(key="file_name", match=MatchValue(value=name))]
                ),
                limit=min(limit, 100),
                offset=offset,
                with_payload=True,
                with_vectors=False
            )
            
            for point in results:
                all_chunks.append({
                    "text": point.payload.get("text", ""),
                    "page": point.payload.get("page_label", "1"),
                    "chunk_index": point.payload.get("chunk_index", 0)
                })
            
            if offset is None or len(all_chunks) >= limit:
                break
        
        # 按頁碼和 chunk_index 排序
        all_chunks.sort(key=lambda x: (int(x.get("page", "1")), x.get("chunk_index", 0)))
        
        return {
            "filename": name,
            "chunks": all_chunks[:limit],
            "total": len(all_chunks)
        }
        
    except Exception as e:
        logger.error(f"Get document content failed: {e}")
        raise HTTPException(500, f"Failed to get content: {str(e)}")


@app.get("/documents/{name}/pdf")
async def get_document_pdf(name: str, download: bool = False):
    """
    獲取原始 PDF 文件
    
    - download=false (預設): 在瀏覽器中預覽 (inline)
    - download=true: 下載文件
    """
    from fastapi.responses import FileResponse
    from pathlib import Path
    
    # PDF 存儲路徑
    pdf_path = Path("data/raw") / name
    
    if not pdf_path.exists():
        raise HTTPException(404, f"PDF file not found: {name}")
    
    # 根據 download 參數決定 Content-Disposition
    if download:
        # 下載模式
        return FileResponse(
            path=str(pdf_path),
            media_type="application/pdf",
            filename=name,
            content_disposition_type="attachment"
        )
    else:
        # 預覽模式 (inline) - 不設定 filename，避免觸發下載
        return FileResponse(
            path=str(pdf_path),
            media_type="application/pdf",
            headers={
                "Content-Disposition": "inline"
            }
        )


@app.delete("/documents/{name}")
async def delete_document(name: str):
    """刪除文件"""
    from services.knowledge_base.service import KnowledgeBaseService
    
    service = KnowledgeBaseService()
    await service.initialize()
    
    result = await service.execute("document_delete", {"document_name": name})
    
    if not result.get("success"):
        raise HTTPException(400, result.get("error", "Delete failed"))
    
    return result


@app.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
):
    """上傳 PDF 文件"""
    import tempfile
    import shutil
    import os as _os
    from pathlib import Path
    
    # 檢查檔案類型
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(400, "Only PDF files are supported")
    
    try:
        # 儲存到 data/raw 目錄
        upload_dir = Path("data/raw")
        upload_dir.mkdir(parents=True, exist_ok=True)
        file_path = upload_dir / file.filename
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # 設定初始狀態
        processing_status[file.filename] = {
            "status": "processing",
            "message": "開始處理文件..."
        }
        
        # 背景處理文件
        async def process_in_background():
            try:
                processing_status[file.filename] = {
                    "status": "processing",
                    "message": "正在解析 PDF (使用 DoclingReader/PyMuPDF)..."
                }
                
                # 使用新的 parser 和 indexer
                from services.knowledge_base.parser import PDFParser
                from services.knowledge_base.indexer import get_indexer
                
                # 1. 初始化
                parser = PDFParser()
                indexer = get_indexer()
                
                # 2. 刪除舊的向量（如果存在）
                deleted = indexer.delete_by_filename(file.filename)
                if deleted > 0:
                    logger.info(f"🗑️ 已刪除 {deleted} 個舊向量")
                
                # 3. 解析 PDF
                processing_status[file.filename] = {
                    "status": "processing",
                    "message": "正在解析 PDF 內容..."
                }
                documents = parser.parse(str(file_path))
                
                if not documents:
                    processing_status[file.filename] = {
                        "status": "error",
                        "message": "PDF 解析失敗，沒有提取到內容"
                    }
                    return
                
                # 4. 索引到 Qdrant
                processing_status[file.filename] = {
                    "status": "processing",
                    "message": f"正在建立索引 ({len(documents)} 個區塊)..."
                }
                indexed = indexer.index_documents(documents)
                
                processing_status[file.filename] = {
                    "status": "completed",
                    "message": f"處理完成！共 {indexed} 個區塊 (使用 {indexer.embed_provider} embedding)"
                }
                logger.info(f"✅ Document processed: {file.filename} ({indexed} chunks)")
                
            except Exception as e:
                processing_status[file.filename] = {
                    "status": "error",
                    "message": f"處理失敗: {str(e)}"
                }
                logger.error(f"❌ Document processing failed: {e}")
                import traceback
                logger.error(traceback.format_exc())
        
        # 加入背景任務
        if background_tasks:
            background_tasks.add_task(process_in_background)
        else:
            # 如果沒有 background_tasks，直接執行
            await process_in_background()
        
        return {
            "success": True,
            "filename": file.filename,
            "status": "processing",
            "message": f"上傳成功，正在處理中..."
        }
        
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(500, f"Upload failed: {str(e)}")


@app.get("/status/{file_name}", response_model=StatusResponse)
async def get_processing_status(file_name: str):
    """取得文件處理狀態"""
    if file_name in processing_status:
        return StatusResponse(
            status=processing_status[file_name]["status"],
            message=processing_status[file_name]["message"]
        )
    return StatusResponse(
        status="unknown",
        message="找不到此文件的處理狀態"
    )


@app.get("/stats")
async def get_stats():
    """取得統計"""
    from services.knowledge_base.service import KnowledgeBaseService
    
    service = KnowledgeBaseService()
    await service.initialize()
    
    return await service.execute("get_stats", {})


@app.get("/debug/qdrant")
async def debug_qdrant():
    """診斷 Qdrant 數據"""
    try:
        from qdrant_client import QdrantClient
        
        client = QdrantClient(host="localhost", port=6333)
        
        # 獲取 collection 信息
        collection_info = client.get_collection("rag_knowledge_base")
        
        # 獲取一些樣本數據
        results, _ = client.scroll(
            collection_name="rag_knowledge_base",
            limit=5,
            with_payload=True,
            with_vectors=False
        )
        
        samples = []
        for point in results:
            samples.append({
                "id": str(point.id),
                "payload_keys": list(point.payload.keys()) if point.payload else [],
                "file_name": point.payload.get("file_name", "NOT_FOUND"),
                "page_label": point.payload.get("page_label", "NOT_FOUND"),
                "text_preview": point.payload.get("text", "")[:100] if point.payload else "",
                "full_payload": point.payload
            })
        
        return {
            "status": "ok",
            "collection": {
                "name": "rag_knowledge_base",
                "points_count": collection_info.points_count,
                "status": str(collection_info.status)
            },
            "samples": samples
        }
        
    except Exception as e:
        import traceback
        return {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }


@app.post("/debug/qdrant/reset")
async def reset_qdrant():
    """重置 Qdrant collection（清空所有數據）"""
    try:
        from qdrant_client import QdrantClient
        from qdrant_client.models import Distance, VectorParams
        import os
        
        client = QdrantClient(host="localhost", port=6333)
        
        # 根據 embedding provider 決定維度
        cohere_key = os.getenv("COHERE_API_KEY")
        if cohere_key:
            embed_dim = 1024  # Cohere embed-multilingual-v3.0
            provider = "Cohere"
        else:
            embed_dim = 1536  # OpenAI text-embedding-3-small
            provider = "OpenAI"
        
        # 刪除舊 collection
        try:
            client.delete_collection("rag_knowledge_base")
            logger.info("🗑️ 已刪除舊 collection")
        except:
            pass
        
        # 創建新 collection
        client.create_collection(
            collection_name="rag_knowledge_base",
            vectors_config=VectorParams(
                size=embed_dim,
                distance=Distance.COSINE
            )
        )
        logger.info(f"✅ 已創建新 collection (維度: {embed_dim}, provider: {provider})")
        
        # 重置全域實例
        from services.knowledge_base.indexer import reset_indexer
        from services.knowledge_base.retriever import reset_retriever
        reset_indexer()
        reset_retriever()
        
        return {
            "status": "ok",
            "message": f"Qdrant collection 已重置 (維度: {embed_dim}, provider: {provider})，請重新上傳 PDF",
            "embed_dim": embed_dim,
            "provider": provider
        }
        
    except Exception as e:
        import traceback
        return {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }


# ============== Tool Execution ==============

@app.post("/execute")
async def execute_tool(
    request: ExecuteRequest,
    eng: OpenCodeEngine = Depends(get_engine)
):
    """直接執行工具"""
    try:
        result = await eng.execute_tool(
            service_id=request.service_id,
            method=request.method,
            params=request.params
        )
        return result
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/services")
async def list_services(eng: OpenCodeEngine = Depends(get_engine)):
    """列出可用服務"""
    return await eng.get_available_services()


# ============== 啟動 ==============

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    )

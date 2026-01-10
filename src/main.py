import logging
import os
import shutil
from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
import asyncio

# 引入核心邏輯
from src.ingestion.pipeline import run_ingestion
from src.retrieval.search import HybridRetriever
from src.retrieval.generation import RAGGenerator
from src.retrieval.agent import RAGAgent

# 🆕 引入 Phase 2 路由
from src.routes_phase2 import router as phase2_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RAG_API")

app = FastAPI(
    title="企業知識庫助手後端 API",
    description="專屬 RAG 後端 API - 支援 Agentic 推理",
    version="3.0.0"
)

# 🆕 加入 Phase 2 路由
app.include_router(phase2_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 設定靜態檔案目錄
app.mount("/files", StaticFiles(directory="data/raw"), name="files")

retriever = None
generator = None
agent = None

# 新增：追蹤文件處理狀態
processing_status = {}

# ============== Pydantic Models ==============

class QueryRequest(BaseModel):
    query: str
    top_k: int = 5

class SearchRequest(BaseModel):
    query: str
    top_k: int = 5

class AskRequest(BaseModel):
    question: str
    top_k: int = 5

class ChatStreamRequest(BaseModel):
    message: str
    selected_docs: Optional[List[str]] = None  # 🆕 支援文件篩選

class SourceDoc(BaseModel):
    file_name: str
    page_label: str
    summary: str
    score: float

class QueryResponse(BaseModel):
    answer: str
    sources: List[SourceDoc]

class UploadResponse(BaseModel):
    message: str
    file_path: str
    file_name: str
    status: str

class StatusResponse(BaseModel):
    status: str
    message: str

class DocumentInfo(BaseModel):
    name: str
    chunks: int
    status: str

class StatsResponse(BaseModel):
    document_count: int
    total_chunks: int
    vector_dim: int
    index_size: str

# ============== Startup ==============

@app.on_event("startup")
async def startup_event():
    global retriever, generator, agent
    retriever = HybridRetriever()
    generator = RAGGenerator()
    agent = RAGAgent(retriever, generator)
    logger.info("✅ RAG 引擎就緒")
    logger.info("✅ RAG Agent 就緒")

# ============== 文件處理 ==============

def process_document(file_path: str, file_name: str):
    global processing_status
    try:
        processing_status[file_name] = {"status": "processing", "message": "正在解析文件..."}
        run_ingestion(file_path)
        processing_status[file_name] = {"status": "completed", "message": "文件處理完成！"}
        logger.info(f"✅ 文件處理完成: {file_name}")
    except Exception as e:
        processing_status[file_name] = {"status": "error", "message": f"處理失敗: {str(e)}"}
        logger.error(f"❌ 文件處理失敗: {e}")

# ============== API Endpoints ==============

@app.post("/upload", response_model=UploadResponse)
async def upload_document(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    upload_dir = os.path.join(os.getcwd(), "data", "raw")
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, file.filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # 設定初始狀態
    processing_status[file.filename] = {"status": "processing", "message": "開始處理文件..."}
    
    # 背景處理
    background_tasks.add_task(process_document, file_path, file.filename)
    
    return UploadResponse(
        message="上傳成功，正在處理中...",
        file_path=file_path,
        file_name=file.filename,
        status="processing"
    )

@app.get("/status/{file_name}", response_model=StatusResponse)
async def get_status(file_name: str):
    if file_name in processing_status:
        return StatusResponse(
            status=processing_status[file_name]["status"],
            message=processing_status[file_name]["message"]
        )
    return StatusResponse(status="unknown", message="找不到此文件的處理狀態")

@app.post("/chat", response_model=QueryResponse)
async def chat_endpoint(request: QueryRequest):
    if not retriever: 
        raise HTTPException(503, "系統初始化中，請稍後再試")
    
    top_k = request.top_k if request.top_k else 5
    results = retriever.search(request.query, top_k=top_k)
    
    if not results:
        return QueryResponse(
            answer="知識庫中尚無資料，請先上傳文件並等待處理完成。",
            sources=[]
        )
    
    ans = generator.generate(request.query, results)
    
    sources = []
    for hit in results:
        payload = hit.payload
        sources.append(SourceDoc(
            file_name=payload.get("file_name", "unknown"),
            page_label=payload.get("page_label", "?"),
            summary=payload.get("text", "")[:100] + "...",
            score=hit.score
        ))
    return QueryResponse(answer=ans, sources=sources)


# ============== 🆕 Agentic 串流 API（支援篩選）==============

@app.post("/chat/stream")
async def chat_stream_endpoint(request: ChatStreamRequest):
    """Agentic RAG 串流對話 - 返回推理過程"""
    if not agent:
        raise HTTPException(503, "Agent 初始化中，請稍後再試")
    
    async def event_generator():
        try:
            # 🆕 傳入 selected_docs
            async for event in agent.chat_stream(request.message, request.selected_docs):
                yield event.to_sse()
        except Exception as e:
            logger.error(f"串流錯誤: {e}")
            import json
            error_payload = {
                "type": "error",
                "content": str(e)
            }
            yield f"data: {json.dumps(error_payload, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


# ============== MCP Server 需要的端點 ==============

@app.post("/search")
async def search_endpoint(request: SearchRequest):
    """語意搜尋 - MCP rag_search 使用"""
    if not retriever:
        raise HTTPException(503, "系統初始化中，請稍後再試")
    
    results = retriever.search(request.query, top_k=request.top_k)
    
    search_results = []
    for hit in results:
        payload = hit.payload
        search_results.append({
            "text": payload.get("text", ""),
            "source": payload.get("file_name", "unknown"),
            "page": payload.get("page_label", "?"),
            "score": hit.score
        })
    
    return search_results


@app.post("/ask")
async def ask_endpoint(request: AskRequest):
    """問答生成 - MCP rag_ask 使用"""
    if not retriever:
        raise HTTPException(503, "系統初始化中，請稍後再試")
    
    results = retriever.search(request.question, top_k=request.top_k)
    
    if not results:
        return {
            "answer": "知識庫中尚無相關資料。",
            "sources": []
        }
    
    answer = generator.generate(request.question, results)
    
    sources = []
    for hit in results:
        payload = hit.payload
        sources.append({
            "source": payload.get("file_name", "unknown"),
            "page": payload.get("page_label", "?"),
            "text": payload.get("text", "")[:150]
        })
    
    return {
        "answer": answer,
        "sources": sources
    }


@app.get("/stats")
async def get_stats():
    """取得知識庫統計 - MCP rag_get_stats 使用"""
    if not retriever:
        raise HTTPException(503, "系統初始化中，請稍後再試")
    
    try:
        from qdrant_client import QdrantClient
        
        client = QdrantClient(host="localhost", port=6333)
        collection_name = "rag_knowledge_base"
        
        # 檢查 collection 是否存在
        collections = client.get_collections().collections
        collection_names = [c.name for c in collections]
        
        if collection_name not in collection_names:
            return StatsResponse(
                document_count=0,
                total_chunks=0,
                vector_dim=0,
                index_size="0 KB"
            )
        
        # 取得 collection 資訊
        collection_info = client.get_collection(collection_name)
        
        # 計算文件數量（從 raw 資料夾）
        raw_dir = "data/raw"
        doc_count = len([f for f in os.listdir(raw_dir) if f.endswith('.pdf')]) if os.path.exists(raw_dir) else 0
        
        return StatsResponse(
            document_count=doc_count,
            total_chunks=collection_info.points_count,
            vector_dim=collection_info.config.params.vectors.size,
            index_size=f"{collection_info.points_count * 1536 * 4 / 1024:.1f} KB"
        )
        
    except Exception as e:
        logger.error(f"取得統計資訊失敗: {e}")
        raise HTTPException(500, f"取得統計資訊失敗: {str(e)}")


# ============== Health Check ==============

@app.get("/health")
async def health_check():
    """健康檢查"""
    return {
        "status": "healthy",
        "retriever": retriever is not None,
        "generator": generator is not None,
        "agent": agent is not None
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8001, reload=True)
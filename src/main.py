import logging
import os
import shutil
from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
import asyncio

# 引入核心邏輯
from src.ingestion.pipeline import run_ingestion
from src.retrieval.search import HybridRetriever
from src.retrieval.generation import RAGGenerator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RAG_API")

app = FastAPI(
    title="企業知識庫助手後端 API",
    description="專屬 RAG 後端 API",
    version="2.0.0"
)

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

# 新增：追蹤文件處理狀態
processing_status = {}

class QueryRequest(BaseModel):
    query: str
    top_k: int = 5

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

@app.on_event("startup")
async def startup_event():
    global retriever, generator
    retriever = HybridRetriever()
    generator = RAGGenerator()
    logger.info("✅ RAG 引擎就緒")

# 新增：同步處理文件的函數
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

# 新增：查詢處理狀態的 endpoint
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8001, reload=True)
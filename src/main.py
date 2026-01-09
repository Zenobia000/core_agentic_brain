import sys
import logging
import time
import json
import shutil
from pathlib import Path
from typing import List, Optional

# --- 1. 路徑修正 (必須在最上面，確保能找到 src) ---
BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR))
# ------------------------------------------------

# --- 2. 第三方套件引用 ---
from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# --- 3. 內部模組引用 ---
# 請確保 src/ingestion/pipeline.py, extractor.py, indexer.py 都存在
from src.retrieval.search import HybridRetriever
from src.retrieval.generation import RAGGenerator
from src.ingestion.pipeline import run_pipeline

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RAG_API")

# --- 4. 初始化 FastAPI (這行必須在 @app 裝飾器之前！) ---
app = FastAPI(
    title="RAG Knowledge Base",
    description="企業級 RAG 知識庫 API，支援 Hybrid Search 與 NQ1D。",
    version="1.0.0"
)

# 開啟 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全域變數
retriever: Optional[HybridRetriever] = None
generator: Optional[RAGGenerator] = None

@app.on_event("startup")
async def startup_event():
    global retriever, generator
    logger.info("🚀 正在初始化 RAG 引擎...")
    try:
        retriever = HybridRetriever()
        generator = RAGGenerator()
        logger.info("✅ RAG 引擎載入完成！")
    except Exception as e:
        logger.error(f"❌ 初始化失敗: {e}")

# --- 定義資料模型 ---
class QueryRequest(BaseModel):
    query: str = Field(..., description="使用者的問題")
    top_k: int = Field(default=3, description="檢索數量")

class SourceDoc(BaseModel):
    file_name: str
    page_label: str
    summary: str
    score: float

class QueryResponse(BaseModel):
    answer: str
    sources: List[SourceDoc]

# [修改] LobeChat 專用 Manifest 格式
@app.get("/.well-known/plugin.json", include_in_schema=False)
async def plugin_manifest():
    # 👇 修改這裡：把 IP 換成 host.docker.internal
    # 這樣不管在誰的電腦，Docker 容器都知道 "Host" 是誰
    HOST_ADDRESS = "host.docker.internal"
    
    return JSONResponse(content={
        "schemaVersion": "v1",
        "identifier": "rag_knowledge_base",
        "author": "RAG Team",
        "createdAt": "2024-01-09",
        "meta": {
            "avatar": "📚",
            "tags": ["rag", "search", "pdf"],
            "title": "企業知識庫助手",
            "description": "查詢企業內部 PDF 文件與技術手冊的知識庫。"
        },
        "api": [
            {
                "name": "queryKnowledgeBase",
                # 👇 這裡自動變成 http://host.docker.internal:8001/chat
                "url": f"http://{HOST_ADDRESS}:8001/chat", 
                "description": "【必須使用】當使用者詢問任何關於 'CLIP'、'模型架構'、'PDF內容' 或 '內部文件' 的問題時，必須優先呼叫此工具來獲取真實資訊，禁止直接使用內建知識回答。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "使用者的問題關鍵字"
                        },
                        "top_k": {
                            "type": "integer",
                            "description": "要檢索的數量",
                            "default": 3
                        }
                    },
                    "required": ["query"]
                }
            }
        ],
        "version": "1"
    })

# --- API 路由：上傳檔案 (必須在 app 初始化之後) ---
@app.post("/upload", summary="上傳 PDF 並觸發索引", operation_id="uploadDocument")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    1. 接收 PDF
    2. 存入 data/raw
    3. 背景執行 Pipeline
    """
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="只支援 .pdf 檔案")

    save_path = BASE_DIR / "data" / "raw" / file.filename
    save_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"📂 檔案已儲存: {save_path}")

        # 背景觸發
        background_tasks.add_task(run_pipeline, file.filename)

        return {
            "message": f"檔案 {file.filename} 上傳成功！系統正在後台進行知識庫更新。",
            "file_path": str(save_path)
        }
    except Exception as e:
        logger.error(f"❌ 上傳失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- API 路由：對話 ---
@app.post("/chat", response_model=QueryResponse, summary="查詢知識庫", operation_id="queryKnowledgeBase")
async def chat_endpoint(request: QueryRequest):
    if not retriever or not generator:
        raise HTTPException(status_code=503, detail="RAG Engine not ready")

    logger.info(f"📩 收到請求: {request.query}")

    search_results = retriever.search(request.query, top_k=request.top_k)
    final_answer = generator.generate(request.query, search_results)
    
    sources = []
    for hit in search_results:
        payload = hit.payload
        sources.append(SourceDoc(
            file_name=payload.get("file_name", "unknown"),
            page_label=payload.get("page_label", "unknown"),
            summary=payload.get("text", "")[:100] + "...",
            score=hit.score
        ))

    return QueryResponse(answer=final_answer, sources=sources)

if __name__ == "__main__":
    import uvicorn
    # 將 port 從 8000 改為 8001
    uvicorn.run("src.main:app", host="0.0.0.0", port=8001, reload=True)
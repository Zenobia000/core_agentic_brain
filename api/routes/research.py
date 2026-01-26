"""
Deep Research API 路由
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/research", tags=["研究"])


# ============== Pydantic Models ==============

class ResearchRequest(BaseModel):
    """研究請求"""
    topic: str
    documents: Optional[List[str]] = None


class ResearchStartResponse(BaseModel):
    """研究啟動回應"""
    task_id: str
    status: str = "started"


# ============== API Endpoints ==============

@router.post("/start", response_model=ResearchStartResponse)
async def start_research(request: ResearchRequest):
    """
    啟動深度研究任務
    
    - **topic**: 研究主題
    - **documents**: 限定文件列表（可選）
    """
    from services.research.service import get_research_service
    
    service = await get_research_service()
    task_id = await service.start_research(
        topic=request.topic,
        documents=request.documents
    )
    
    return ResearchStartResponse(task_id=task_id)


@router.get("/{task_id}")
async def get_research_status(task_id: str):
    """
    取得研究任務狀態
    
    - **task_id**: 研究任務 ID
    """
    from services.research.service import get_research_service
    
    service = await get_research_service()
    task = await service.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return task.to_dict()


@router.get("")
async def list_research_tasks():
    """列出所有研究任務"""
    from services.research.service import get_research_service
    
    service = await get_research_service()
    tasks = await service.list_tasks()
    
    return {"tasks": tasks}

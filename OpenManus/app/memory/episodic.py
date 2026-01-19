"""
Episodic Memory - 情節記憶 (任務歷史)
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskRecord(BaseModel):
    """任務記錄 - 對應 task_N_output.json"""
    
    task_id: str
    goal: str
    status: TaskStatus = TaskStatus.PENDING
    
    created_at: datetime = Field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    steps: List[Dict[str, Any]] = Field(default_factory=list)
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list)
    
    result: Optional[str] = None
    artifacts: List[str] = Field(default_factory=list)
    error: Optional[str] = None
    
    success_criteria: List[str] = Field(default_factory=list)
    token_usage: Dict[str, int] = Field(default_factory=lambda: {"input": 0, "output": 0, "total": 0})
    duration_seconds: Optional[float] = None
    
    class Config:
        use_enum_values = True
    
    def add_step(self, step_type: str, content: str) -> None:
        self.steps.append({
            "step_number": len(self.steps) + 1,
            "type": step_type,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
    
    def add_tool_call(self, tool_name: str, arguments: Dict, result: Any, success: bool) -> None:
        self.tool_calls.append({
            "tool_name": tool_name,
            "arguments": arguments,
            "result": result,
            "success": success,
            "timestamp": datetime.now().isoformat()
        })
    
    def start(self) -> None:
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.now()
    
    def complete(self, result: str, artifacts: Optional[List[str]] = None) -> None:
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.now()
        self.result = result
        if artifacts:
            self.artifacts = artifacts
        if self.started_at:
            self.duration_seconds = (self.completed_at - self.started_at).total_seconds()
    
    def fail(self, error: str) -> None:
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.now()
        self.error = error
    
    def to_summary(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "goal": self.goal,
            "status": self.status,
            "result_preview": self.result[:200] + "..." if self.result and len(self.result) > 200 else self.result,
            "steps_count": len(self.steps),
            "duration_seconds": self.duration_seconds,
        }


class EpisodicMemory(BaseModel):
    """情節記憶管理器"""
    
    tasks: Dict[str, TaskRecord] = Field(default_factory=dict)
    storage_path: Optional[Path] = None
    max_tasks: int = 100
    auto_persist: bool = True
    
    class Config:
        arbitrary_types_allowed = True
    
    def __init__(self, storage_path: Optional[str] = None, **data):
        super().__init__(**data)
        if storage_path:
            self.storage_path = Path(storage_path)
            self.storage_path.mkdir(parents=True, exist_ok=True)
            self._load_from_disk()
    
    def create_task(self, goal: str, task_id: Optional[str] = None) -> TaskRecord:
        if task_id is None:
            task_id = f"task_{len(self.tasks) + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        task = TaskRecord(task_id=task_id, goal=goal)
        self.tasks[task_id] = task
        
        if self.auto_persist and self.storage_path:
            self._persist_task(task)
        
        return task
    
    def get_task(self, task_id: str) -> Optional[TaskRecord]:
        return self.tasks.get(task_id)
    
    def get_recent_tasks(self, n: int = 10) -> List[TaskRecord]:
        sorted_tasks = sorted(self.tasks.values(), key=lambda t: t.created_at, reverse=True)
        return sorted_tasks[:n]
    
    def get_similar_tasks(self, goal: str, limit: int = 5) -> List[TaskRecord]:
        goal_words = set(goal.lower().split())
        scored = []
        for task in self.tasks.values():
            task_words = set(task.goal.lower().split())
            overlap = len(goal_words & task_words)
            if overlap > 0:
                scored.append((overlap, task))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [t for _, t in scored[:limit]]
    
    def get_statistics(self) -> Dict[str, Any]:
        total = len(self.tasks)
        if total == 0:
            return {"total": 0}
        completed = len([t for t in self.tasks.values() if t.status == TaskStatus.COMPLETED])
        return {
            "total": total,
            "completed": completed,
            "success_rate": completed / total if total > 0 else 0,
        }
    
    def _persist_task(self, task: TaskRecord) -> None:
        if self.storage_path:
            task_file = self.storage_path / f"{task.task_id}.json"
            with open(task_file, "w", encoding="utf-8") as f:
                json.dump(task.model_dump(), f, ensure_ascii=False, indent=2, default=str)
    
    def _load_from_disk(self) -> None:
        if self.storage_path and self.storage_path.exists():
            for task_file in self.storage_path.glob("*.json"):
                try:
                    with open(task_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        task = TaskRecord(**data)
                        self.tasks[task.task_id] = task
                except Exception as e:
                    print(f"Warning: Failed to load task from {task_file}: {e}")

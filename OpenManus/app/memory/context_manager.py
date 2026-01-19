"""
Context Manager - 上下文工程管理器
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from app.memory.short_term import ShortTermMemory
from app.memory.episodic import EpisodicMemory, TaskRecord
from app.memory.long_term import LongTermMemory, RetrievalResult


class ContextWindow(BaseModel):
    """上下文窗口"""
    
    system_prompt: Optional[str] = None
    knowledge_context: List[str] = Field(default_factory=list)
    experience_context: List[Dict[str, Any]] = Field(default_factory=list)
    conversation_history: List[Dict[str, str]] = Field(default_factory=list)
    current_task: Optional[Dict[str, Any]] = None
    total_tokens_estimate: int = 0
    assembled_at: datetime = Field(default_factory=datetime.now)
    
    def to_messages(self) -> List[Dict[str, str]]:
        """轉換為 LLM 訊息格式"""
        messages = []
        
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        
        if self.knowledge_context:
            knowledge_text = "\n\n".join([f"[Knowledge {i+1}]\n{k}" for i, k in enumerate(self.knowledge_context)])
            messages.append({"role": "system", "content": f"## Relevant Knowledge:\n{knowledge_text}"})
        
        if self.experience_context:
            exp_text = "\n\n".join([f"[Past Task: {e.get('goal', 'N/A')}]\nResult: {e.get('result_preview', 'N/A')}" for e in self.experience_context])
            messages.append({"role": "system", "content": f"## Past Experiences:\n{exp_text}"})
        
        if self.current_task:
            task_text = f"## Current Task:\nGoal: {self.current_task.get('goal', 'N/A')}"
            messages.append({"role": "system", "content": task_text})
        
        messages.extend(self.conversation_history)
        return messages


class ContextManager(BaseModel):
    """上下文工程管理器 - 統一管理三層記憶"""
    
    short_term: ShortTermMemory = Field(default_factory=ShortTermMemory)
    episodic: Optional[EpisodicMemory] = None
    long_term: Optional[LongTermMemory] = None
    
    max_context_tokens: int = 8000
    knowledge_top_k: int = 3
    experience_top_k: int = 2
    
    _shared_contexts: Dict[str, "ContextManager"] = {}
    
    class Config:
        arbitrary_types_allowed = True
    
    async def initialize(self, episodic_path: Optional[str] = None) -> None:
        if self.episodic is None:
            self.episodic = EpisodicMemory(storage_path=episodic_path)
        if self.long_term is None:
            self.long_term = LongTermMemory()
            await self.long_term.initialize()
    
    async def assemble_context(
        self,
        query: str,
        system_prompt: Optional[str] = None,
        current_task: Optional[TaskRecord] = None,
        include_knowledge: bool = True,
        include_experience: bool = True,
    ) -> ContextWindow:
        """智慧組裝上下文窗口"""
        context = ContextWindow(system_prompt=system_prompt)
        tokens_used = len(system_prompt or "") // 4
        
        # 1. 檢索相關知識
        if include_knowledge and self.long_term:
            try:
                results = await self.long_term.retrieve(query, self.knowledge_top_k)
                for r in results:
                    content = r.document.content
                    if tokens_used + len(content) // 4 < self.max_context_tokens * 0.3:
                        context.knowledge_context.append(content)
                        tokens_used += len(content) // 4
            except Exception:
                pass
        
        # 2. 檢索相關經驗
        if include_experience and self.episodic:
            similar = self.episodic.get_similar_tasks(query, self.experience_top_k)
            for task in similar:
                summary = task.to_summary()
                if tokens_used + 100 < self.max_context_tokens * 0.5:
                    context.experience_context.append(summary)
                    tokens_used += 100
        
        # 3. 當前任務
        if current_task:
            context.current_task = {"goal": current_task.goal}
        
        # 4. 對話歷史
        remaining = self.max_context_tokens - tokens_used
        conversation = self.short_term.get_context_window(remaining)
        context.conversation_history = [{"role": m.role, "content": m.content or ""} for m in conversation]
        
        context.total_tokens_estimate = tokens_used
        return context
    
    def add_message(self, role: str, content: str) -> None:
        if role == "user":
            self.short_term.add_user_message(content)
        elif role == "assistant":
            self.short_term.add_assistant_message(content)
    
    def create_task(self, goal: str, **kwargs) -> TaskRecord:
        if self.episodic is None:
            self.episodic = EpisodicMemory()
        return self.episodic.create_task(goal, **kwargs)
    
    async def store_knowledge(self, content: str, source: Optional[str] = None) -> str:
        if self.long_term is None:
            self.long_term = LongTermMemory()
            await self.long_term.initialize()
        return await self.long_term.store(content, source)
    
    @classmethod
    def get_shared_context(cls, context_id: str) -> Optional["ContextManager"]:
        return cls._shared_contexts.get(context_id)
    
    @classmethod
    def share_context(cls, context_id: str, context: "ContextManager") -> None:
        cls._shared_contexts[context_id] = context

"""
Short-term Memory - 短期記憶 (對話上下文)
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from app.schema import Memory as BaseMemory, Message


class ShortTermMemory(BaseModel):
    """短期記憶管理器"""
    
    base_memory: BaseMemory = Field(default_factory=BaseMemory)
    max_tokens: int = Field(default=8000)
    max_messages: int = Field(default=50)
    created_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        arbitrary_types_allowed = True
    
    def add_message(self, message: Message) -> None:
        self.base_memory.add_message(message)
        self._enforce_limits()
    
    def add_user_message(self, content: str) -> None:
        self.add_message(Message.user_message(content))
    
    def add_assistant_message(self, content: str) -> None:
        self.add_message(Message.assistant_message(content))
    
    @property
    def messages(self) -> List[Message]:
        return self.base_memory.messages
    
    def get_recent(self, n: int = 10) -> List[Message]:
        return self.messages[-n:] if len(self.messages) >= n else self.messages
    
    def get_context_window(self, max_tokens: Optional[int] = None) -> List[Message]:
        """取得適合上下文窗口的訊息"""
        target_tokens = max_tokens or self.max_tokens
        system_msgs = [m for m in self.messages if m.role == "system"]
        other_msgs = [m for m in self.messages if m.role != "system"]
        
        selected = []
        current_tokens = sum(len(m.content or "") // 4 for m in system_msgs)
        
        for msg in reversed(other_msgs):
            msg_tokens = len(msg.content or "") // 4
            if current_tokens + msg_tokens <= target_tokens:
                selected.insert(0, msg)
                current_tokens += msg_tokens
            else:
                break
        
        return system_msgs + selected
    
    def _enforce_limits(self) -> None:
        while len(self.messages) > self.max_messages:
            for i, msg in enumerate(self.messages):
                if msg.role != "system":
                    self.base_memory.messages.pop(i)
                    break
    
    def clear(self) -> None:
        self.base_memory.messages.clear()
    
    def __len__(self) -> int:
        return len(self.messages)

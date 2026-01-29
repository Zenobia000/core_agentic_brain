"""
統一溝通協議 - 極簡實作 (< 100 行)
基於 Linus 原則：消除特殊情況，統一處理
"""

from typing import Any, Dict, Optional, List
from dataclasses import dataclass
from enum import Enum


class MessageType(Enum):
    """訊息類型 - 沒有特殊情況"""
    PROMPT = "prompt"
    TOOL_CALL = "tool_call"
    RESULT = "result"
    ERROR = "error"


@dataclass
class Message:
    """統一訊息格式 - 沒有特殊情況"""
    type: MessageType
    content: Any
    source: str
    target: str
    metadata: Dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class CommunicationBus:
    """中央通訊匯流排 - 單一真相來源"""

    def __init__(self):
        """初始化通訊匯流排"""
        self.handlers = {}  # 統一的處理器註冊表
        self.history: List[Message] = []  # 訊息歷史

    def register(self, id: str, handler: Any):
        """註冊處理器 - 統一介面

        Args:
            id: 處理器識別符
            handler: 必須有 handle(message) 方法
        """
        if not hasattr(handler, 'handle'):
            raise ValueError(f"Handler {id} must have handle() method")
        self.handlers[id] = handler

    async def send(self, message: Message) -> Any:
        """發送訊息 - 沒有 if/else 特殊處理

        Args:
            message: 要發送的訊息

        Returns:
            處理結果
        """
        # 記錄訊息
        self.history.append(message)

        # 統一的接收者查找
        if handler := self.handlers.get(message.target):
            # 統一的處理方式
            import asyncio
            if asyncio.iscoroutinefunction(handler.handle):
                return await handler.handle(message)
            else:
                return handler.handle(message)
        else:
            error_msg = Message(
                type=MessageType.ERROR,
                content=f"Handler not found: {message.target}",
                source="bus",
                target=message.source
            )
            self.history.append(error_msg)
            return error_msg

    def get_history(self, filter_type: MessageType = None) -> List[Message]:
        """獲取訊息歷史

        Args:
            filter_type: 篩選特定類型的訊息

        Returns:
            訊息列表
        """
        if filter_type:
            return [m for m in self.history if m.type == filter_type]
        return self.history.copy()
"""
純函數工具基類 - 極簡實作 (< 50 行)
基於 Linus 原則：工具不應該知道提示詞，只做一件事
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Union, Coroutine, TYPE_CHECKING
from core.communication import Message, MessageType

if TYPE_CHECKING:
    from core.types import TaskContext


class PureTool(ABC):
    """純函數工具基類 - 無狀態，工作區感知，支援同步/異步執行"""

    def __init__(self):
        """初始化工具 - 只設定基本屬性"""
        self.name = self.__class__.__name__.lower().replace('tool', '')

    @property
    @abstractmethod
    def definition(self) -> Dict:
        """工具定義 - 純資料，不依賴外部"""
        pass

    @abstractmethod
    def execute(
        self,
        parameters: Dict[str, Any],
        context: Optional["TaskContext"] = None
    ) -> Union[Dict, Coroutine[Any, Any, Dict]]:
        """執行工具 - 工作區感知，可以是同步或異步

        Args:
            parameters: 工具參數
            context: 任務上下文（包含 workspace_path）

        Returns:
            執行結果字典（或返回協程）
        """
        pass

    async def handle(self, message: Message) -> Any:
        """處理訊息 - 統一介面給 CommunicationBus 使用（異步）

        Args:
            message: 來自 bus 的訊息

        Returns:
            處理結果
        """
        if message.type != MessageType.TOOL_CALL:
            return {
                "error": f"Tool {self.name} can only handle TOOL_CALL messages"
            }

        # 從 message.metadata 提取 context
        context = message.metadata.get("context") if message.metadata else None

        # 執行工具，傳遞 context - 支援同步和異步
        result = self.execute(message.content, context)

        # 如果 execute 返回協程，等待它
        if asyncio.iscoroutine(result):
            return await result
        return result
"""
純函數工具基類 - 極簡實作 (< 50 行)
基於 Linus 原則：工具不應該知道提示詞，只做一件事
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
from core.communication import Message, MessageType


class PureTool(ABC):
    """純函數工具基類 - 無狀態，無副作用"""

    def __init__(self):
        """初始化工具 - 只設定基本屬性"""
        self.name = self.__class__.__name__.lower().replace('tool', '')

    @property
    @abstractmethod
    def definition(self) -> Dict:
        """工具定義 - 純資料，不依賴外部"""
        pass

    @abstractmethod
    def execute(self, parameters: Dict[str, Any]) -> Dict:
        """執行工具 - 純函數，輸入輸出明確

        Args:
            parameters: 工具參數

        Returns:
            執行結果字典
        """
        pass

    def handle(self, message: Message) -> Any:
        """處理訊息 - 統一介面給 CommunicationBus 使用

        Args:
            message: 來自 bus 的訊息

        Returns:
            處理結果
        """
        if message.type != MessageType.TOOL_CALL:
            return {
                "error": f"Tool {self.name} can only handle TOOL_CALL messages"
            }

        # 執行純函數
        return self.execute(message.content)
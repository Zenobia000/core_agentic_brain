"""
工具基類 - 所有工具的抽象介面
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseTool(ABC):
    """所有工具必須繼承的基類"""

    @property
    @abstractmethod
    def definition(self) -> Dict:
        """工具定義（OpenAI function calling 格式）

        Returns:
            包含工具名稱、描述、參數的字典
        """
        pass

    @abstractmethod
    async def execute(self, parameters: Dict[str, Any]) -> Dict:
        """執行工具

        Args:
            parameters: 工具執行參數

        Returns:
            執行結果字典
        """
        pass

    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """驗證參數（可選實作）

        Args:
            parameters: 待驗證的參數

        Returns:
            參數是否有效
        """
        return True
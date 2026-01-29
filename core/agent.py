"""
Core Agent - 極簡實作 (< 100 行)
基於 Linus 式設計原則：簡潔、實用、無過度設計
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from .llm import LLMWrapper
from .tools import ToolManager


@dataclass
class AgentResponse:
    """Agent 回應結構"""
    content: str
    tool_calls: Optional[List[Dict]] = None


class Agent:
    """極簡 Agent 核心 - Layer 0"""

    def __init__(self, config: Dict[str, Any] = None):
        """初始化 Agent

        Args:
            config: 配置字典，可選
        """
        from .utils import get_config_value

        self.config = config or self._default_config()

        # 消除特殊情況 - 統一處理 nested 和 flat config
        llm_config = get_config_value(self.config, "core", "llm") or \
                     get_config_value(self.config, "llm")
        tools_config = get_config_value(self.config, "core", "tools") or \
                       get_config_value(self.config, "tools")

        self.llm = LLMWrapper(llm_config)
        self.tools = ToolManager(tools_config)
        self.messages = []  # 對話歷史

    async def process(self, user_input: str) -> str:
        """處理用戶輸入 - 核心邏輯

        Args:
            user_input: 用戶輸入文字

        Returns:
            AI 回應文字
        """
        # 1. 添加用戶訊息
        self.messages.append({"role": "user", "content": user_input})

        # 2. 準備工具定義
        tool_defs = self.tools.get_definitions() if self.tools.enabled else None

        # 3. 呼叫 LLM
        response = await self.llm.generate(self.messages, tool_defs)

        # 4. 處理工具調用
        if response.tool_calls:
            tool_results = await self._execute_tools(response.tool_calls)
            # 將工具結果加入上下文
            self.messages.extend(tool_results)
            # 再次呼叫 LLM 獲取最終回應
            response = await self.llm.generate(self.messages)

        # 5. 更新對話歷史
        self.messages.append({"role": "assistant", "content": response.content})

        # 6. 控制歷史長度（避免記憶體溢出）
        if len(self.messages) > 20:
            self.messages = self.messages[-10:]

        return response.content

    async def _execute_tools(self, tool_calls: List[Any]) -> List[Dict]:
        """執行工具調用

        Args:
            tool_calls: 工具調用列表

        Returns:
            工具執行結果列表
        """
        results = []
        for call in tool_calls:
            # Handle both dict and object types
            if hasattr(call, 'function'):
                # OpenAI SDK object
                name = call.function.name
                parameters = call.function.arguments if isinstance(call.function.arguments, dict) else {}
                call_id = call.id
            else:
                # Dictionary format
                name = call.get("name") or call.get("function", {}).get("name")
                parameters = call.get("parameters", {}) or call.get("function", {}).get("arguments", {})
                call_id = call.get("id")

            result = await self.tools.execute(
                name=name,
                parameters=parameters
            )
            results.append({
                "role": "tool",
                "content": str(result),
                "tool_call_id": call_id
            })
        return results

    def _default_config(self) -> Dict[str, Any]:
        """預設配置"""
        return {
            "llm": {
                "provider": "openai",
                "model": "gpt-3.5-turbo",
                "temperature": 0.7
            },
            "tools": {
                "enabled": ["python", "files"]
            }
        }

    def reset(self):
        """重置對話歷史"""
        self.messages = []

    # 同步包裝器（為了相容現有 main.py）
    def run(self, user_query: str) -> str:
        """同步執行介面（向後相容）"""
        import asyncio
        return asyncio.run(self.process(user_query))
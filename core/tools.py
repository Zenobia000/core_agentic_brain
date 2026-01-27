"""
工具管理器 - 極簡實作 (< 50 行)
動態載入和執行工具
"""

from typing import Dict, List, Any, Optional
import importlib


class ToolManager:
    """工具註冊與執行管理"""

    def __init__(self, config: Dict[str, Any]):
        """初始化工具管理器

        Args:
            config: 工具配置，包含 enabled 列表
        """
        self.enabled = config.get("enabled", [])
        self.tools = {}
        self._load_tools()

    def _load_tools(self):
        """動態載入啟用的工具"""
        for tool_name in self.enabled:
            try:
                # 嘗試從 tools 目錄載入
                module = importlib.import_module(f"tools.{tool_name}")
                if hasattr(module, 'Tool'):
                    self.tools[tool_name] = module.Tool()
                else:
                    print(f"Warning: Tool {tool_name} has no Tool class")
            except ImportError as e:
                print(f"Warning: Could not load tool {tool_name}: {e}")

    def get_definitions(self) -> List[Dict]:
        """獲取所有工具的定義（for LLM）"""
        definitions = []
        for tool in self.tools.values():
            if hasattr(tool, 'definition'):
                definitions.append(tool.definition)
        return definitions

    async def execute(self, name: str, parameters: Dict) -> Dict:
        """執行指定的工具

        Args:
            name: 工具名稱
            parameters: 工具參數

        Returns:
            執行結果字典
        """
        if tool := self.tools.get(name):
            try:
                # 如果工具有 async execute 方法
                if hasattr(tool, 'execute'):
                    import asyncio
                    if asyncio.iscoroutinefunction(tool.execute):
                        return await tool.execute(parameters)
                    else:
                        return tool.execute(parameters)
            except Exception as e:
                return {"error": f"Tool execution failed: {str(e)}"}
        return {"error": f"Tool {name} not found"}
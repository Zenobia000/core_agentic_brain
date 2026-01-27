"""
Python 程式碼執行工具 - 極簡實作 (< 50 行)
安全地執行 Python 程式碼
"""

import io
import contextlib
from typing import Dict, Any


class Tool:
    """Python 執行工具"""

    @property
    def definition(self) -> Dict:
        """工具定義（OpenAI function 格式）"""
        return {
            "type": "function",
            "function": {
                "name": "python",
                "description": "Execute Python code and return the output",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "The Python code to execute"
                        }
                    },
                    "required": ["code"]
                }
            }
        }

    async def execute(self, parameters: Dict[str, Any]) -> Dict:
        """執行 Python 程式碼

        Args:
            parameters: 包含 'code' 鍵的參數字典

        Returns:
            執行結果字典
        """
        code = parameters.get("code", "")

        # 創建輸出捕獲
        output = io.StringIO()

        try:
            # 使用受限的執行環境
            with contextlib.redirect_stdout(output):
                # 執行代碼
                exec(code, {"__builtins__": self._safe_builtins()})

            return {
                "success": True,
                "output": output.getvalue()
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _safe_builtins(self) -> Dict:
        """返回安全的內建函數集"""
        import builtins
        # 只允許安全的內建函數
        safe_list = [
            'abs', 'all', 'any', 'ascii', 'bin', 'bool', 'chr', 'dict',
            'dir', 'divmod', 'enumerate', 'filter', 'float', 'format',
            'hex', 'int', 'isinstance', 'len', 'list', 'map', 'max', 'min',
            'oct', 'ord', 'pow', 'print', 'range', 'repr', 'reversed',
            'round', 'set', 'slice', 'sorted', 'str', 'sum', 'tuple', 'type', 'zip'
        ]
        return {name: getattr(builtins, name) for name in safe_list}
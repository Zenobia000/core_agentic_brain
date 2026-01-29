"""
Python 程式碼執行工具 - 純函數版本 (< 80 行)
基於 Linus 原則：工具只做一件事，不知道提示詞
"""

import io
import contextlib
import traceback
from typing import Dict, Any
from tools.pure_base import PureTool


class Tool(PureTool):
    """Python 執行工具 - 純函數，無狀態"""

    def __init__(self):
        """初始化 Python 工具"""
        super().__init__()
        self.name = "python"

    @property
    def definition(self) -> Dict:
        """工具定義 - 純資料"""
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

    def execute(self, parameters: Dict[str, Any]) -> Dict:
        """執行 Python 程式碼 - 純函數實作

        Args:
            parameters: 包含 'code' 鍵的參數字典

        Returns:
            執行結果字典
        """
        # 獲取程式碼
        code = parameters.get("code", "")
        if not code:
            return {"error": "No code provided", "output": ""}

        # 捕獲輸出
        output_buffer = io.StringIO()

        try:
            # 重定向標準輸出
            with contextlib.redirect_stdout(output_buffer):
                # 創建安全的執行環境
                safe_globals = {
                    "__builtins__": __builtins__,
                    "__name__": "__main__"
                }

                # 執行程式碼
                exec(code, safe_globals)

            # 獲取輸出
            output = output_buffer.getvalue()
            return {
                "success": True,
                "output": output,
                "error": None
            }

        except Exception as e:
            # 返回錯誤信息
            error_msg = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
            return {
                "success": False,
                "output": output_buffer.getvalue(),
                "error": error_msg
            }
        finally:
            output_buffer.close()
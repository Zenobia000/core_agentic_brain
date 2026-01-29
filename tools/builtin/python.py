"""
Python 程式碼執行工具 - 工作區感知版本
基於 Linus 原則：工具只做一件事，安全操作在沙箱內
"""

import io
import os
import contextlib
import traceback
from pathlib import Path
from typing import Dict, Any, Optional, TYPE_CHECKING
from ..pure_base import PureTool

if TYPE_CHECKING:
    from core.types import TaskContext


class Tool(PureTool):
    """Python 執行工具 - 工作區感知，CWD 受限"""

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
                "description": "Execute Python code within workspace. File operations use workspace paths.",
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

    def execute(
        self,
        parameters: Dict[str, Any],
        context: Optional["TaskContext"] = None
    ) -> Dict:
        """執行 Python 程式碼 - 工作區感知

        Args:
            parameters: 包含 'code' 鍵的參數字典
            context: 任務上下文（包含 workspace_path）

        Returns:
            執行結果字典
        """
        # 獲取程式碼
        code = parameters.get("code", "")
        if not code:
            return {"error": "No code provided", "output": "", "success": False}

        # 獲取工作區路徑
        workspace_path = None
        if context and context.workspace_path:
            workspace_path = context.workspace_path

        # 保存當前工作目錄
        original_cwd = os.getcwd()

        # 捕獲輸出
        output_buffer = io.StringIO()

        try:
            # 切換到工作區目錄（如果有）
            if workspace_path:
                os.chdir(workspace_path)

            # 重定向標準輸出
            with contextlib.redirect_stdout(output_buffer):
                # 創建安全的執行環境
                safe_globals = {
                    "__builtins__": __builtins__,
                    "__name__": "__main__",
                }

                # 如果有工作區，注入路徑資訊
                if workspace_path:
                    safe_globals["WORKSPACE"] = workspace_path
                    safe_globals["INPUT_DIR"] = workspace_path / "input"
                    safe_globals["OUTPUT_DIR"] = workspace_path / "output"
                    safe_globals["TEMP_DIR"] = workspace_path / "temp"

                # 執行程式碼
                exec(code, safe_globals)

            # 獲取輸出
            output = output_buffer.getvalue()
            result = {
                "success": True,
                "output": output,
                "error": None
            }
            if workspace_path:
                result["workspace"] = str(workspace_path)
            return result

        except Exception as e:
            # 返回錯誤信息
            error_msg = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
            return {
                "success": False,
                "output": output_buffer.getvalue(),
                "error": error_msg
            }
        finally:
            # 恢復原始工作目錄
            os.chdir(original_cwd)
            output_buffer.close()
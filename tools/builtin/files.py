"""
檔案操作工具 - 純函數版本 (< 100 行)
基於 Linus 原則：工具只做一件事，不知道提示詞
"""

import os
from pathlib import Path
from typing import Dict, Any
from ..pure_base import PureTool


class Tool(PureTool):
    """檔案操作工具 - 純函數，無狀態"""

    def __init__(self):
        """初始化檔案工具"""
        super().__init__()
        self.name = "files"

    @property
    def definition(self) -> Dict:
        """工具定義 - 純資料"""
        return {
            "type": "function",
            "function": {
                "name": "files",
                "description": "Perform file operations: read, write, list, delete",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "operation": {
                            "type": "string",
                            "enum": ["read", "write", "list", "delete", "exists"],
                            "description": "The file operation to perform"
                        },
                        "path": {
                            "type": "string",
                            "description": "The file or directory path"
                        },
                        "content": {
                            "type": "string",
                            "description": "Content to write (for write operation)"
                        }
                    },
                    "required": ["operation", "path"]
                }
            }
        }

    def execute(self, parameters: Dict[str, Any]) -> Dict:
        """執行檔案操作 - 純函數實作

        Args:
            parameters: 包含 operation, path, content 的參數

        Returns:
            執行結果字典
        """
        operation = parameters.get("operation")
        path = parameters.get("path", "")

        if not operation:
            return {"success": False, "error": "No operation specified"}

        if not path:
            return {"success": False, "error": "No path specified"}

        try:
            if operation == "read":
                return self._read_file(path)
            elif operation == "write":
                content = parameters.get("content", "")
                return self._write_file(path, content)
            elif operation == "list":
                return self._list_directory(path)
            elif operation == "delete":
                return self._delete_file(path)
            elif operation == "exists":
                return self._check_exists(path)
            else:
                return {"success": False, "error": f"Unknown operation: {operation}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _read_file(self, path: str) -> Dict:
        """讀取檔案"""
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        return {"success": True, "content": content}

    def _write_file(self, path: str, content: str) -> Dict:
        """寫入檔案"""
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return {"success": True, "message": f"Written to {path}"}

    def _list_directory(self, path: str) -> Dict:
        """列出目錄內容"""
        items = list(Path(path).iterdir())
        return {
            "success": True,
            "items": [str(item) for item in items]
        }

    def _delete_file(self, path: str) -> Dict:
        """刪除檔案"""
        os.remove(path)
        return {"success": True, "message": f"Deleted {path}"}

    def _check_exists(self, path: str) -> Dict:
        """檢查檔案是否存在"""
        exists = Path(path).exists()
        return {"success": True, "exists": exists}
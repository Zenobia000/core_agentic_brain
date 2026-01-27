"""
檔案操作工具 - 極簡實作 (< 50 行)
安全的檔案系統操作
"""

import os
from pathlib import Path
from typing import Dict, Any


class Tool:
    """檔案系統操作工具"""

    @property
    def definition(self) -> Dict:
        """工具定義"""
        return {
            "type": "function",
            "function": {
                "name": "files",
                "description": "Perform file system operations (read, write, list)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "operation": {
                            "type": "string",
                            "enum": ["read", "write", "list"],
                            "description": "The operation to perform"
                        },
                        "path": {
                            "type": "string",
                            "description": "The file or directory path"
                        },
                        "content": {
                            "type": "string",
                            "description": "Content for write operation (optional)"
                        }
                    },
                    "required": ["operation", "path"]
                }
            }
        }

    async def execute(self, parameters: Dict[str, Any]) -> Dict:
        """執行檔案操作"""
        operation = parameters.get("operation")
        path_str = parameters.get("path", ".")

        # 安全檢查 - 確保路徑在工作目錄內
        try:
            path = Path(path_str).resolve()
            work_dir = Path.cwd()
            if not str(path).startswith(str(work_dir)):
                return {"error": "Access denied: Path outside working directory"}
        except Exception:
            return {"error": "Invalid path"}

        try:
            if operation == "read":
                with open(path, 'r', encoding='utf-8') as f:
                    return {"content": f.read()}

            elif operation == "write":
                content = parameters.get("content", "")
                # 確保父目錄存在
                path.parent.mkdir(parents=True, exist_ok=True)
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return {"success": True, "message": f"File written: {path}"}

            elif operation == "list":
                if path.is_file():
                    return {"error": "Path is a file, not a directory"}
                items = []
                for item in path.iterdir():
                    items.append({
                        "name": item.name,
                        "type": "directory" if item.is_dir() else "file",
                        "size": item.stat().st_size if item.is_file() else None
                    })
                return {"items": sorted(items, key=lambda x: (x["type"] != "directory", x["name"]))}

            else:
                return {"error": f"Unknown operation: {operation}"}

        except Exception as e:
            return {"error": str(e)}
"""
檔案操作工具 - 工作區感知版本
基於 Linus 原則：工具只做一件事，安全操作在沙箱內
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional, TYPE_CHECKING
from ..pure_base import PureTool

if TYPE_CHECKING:
    from core.types import TaskContext


class Tool(PureTool):
    """檔案操作工具 - 工作區感知，安全隔離"""

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
                "description": "Perform file operations within workspace: read, write, list, delete. Paths are relative to workspace.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "operation": {
                            "type": "string",
                            "enum": ["read", "write", "list", "delete", "exists"],
                            "description": "The file operation to perform"
                        },
                        "filename": {
                            "type": "string",
                            "description": "Relative filename within workspace (e.g., 'output.txt', 'data/result.json')"
                        },
                        "content": {
                            "type": "string",
                            "description": "Content to write (for write operation)"
                        },
                        "subdir": {
                            "type": "string",
                            "enum": ["input", "output", "temp"],
                            "description": "Workspace subdirectory (default: output for write, auto-search for read)"
                        }
                    },
                    "required": ["operation", "filename"]
                }
            }
        }

    def execute(
        self,
        parameters: Dict[str, Any],
        context: Optional["TaskContext"] = None
    ) -> Dict:
        """執行檔案操作 - 工作區感知

        Args:
            parameters: 包含 operation, filename, content, subdir 的參數
            context: 任務上下文（包含 workspace_path）

        Returns:
            執行結果字典
        """
        operation = parameters.get("operation")
        # Support both 'filename' (new) and 'path' (legacy)
        filename = parameters.get("filename") or parameters.get("path", "")

        if not operation:
            return {"success": False, "error": "No operation specified"}

        if not filename:
            return {"success": False, "error": "No filename specified"}

        # Resolve path based on workspace context
        workspace_path = context.workspace_path if context and context.workspace_path else None

        try:
            if operation == "read":
                return self._read_file(filename, workspace_path)
            elif operation == "write":
                content = parameters.get("content", "")
                subdir = parameters.get("subdir", "output")
                return self._write_file(filename, content, workspace_path, subdir)
            elif operation == "list":
                subdir = parameters.get("subdir", "output")
                return self._list_directory(filename, workspace_path, subdir)
            elif operation == "delete":
                subdir = parameters.get("subdir", "output")
                return self._delete_file(filename, workspace_path, subdir)
            elif operation == "exists":
                return self._check_exists(filename, workspace_path)
            else:
                return {"success": False, "error": f"Unknown operation: {operation}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _resolve_read_path(
        self,
        filename: str,
        workspace_path: Optional[Path]
    ) -> Path:
        """Resolve path for reading, searching workspace subdirs."""
        if workspace_path:
            # Search order: input > output > temp
            for subdir in ["input", "output", "temp"]:
                candidate = workspace_path / subdir / filename
                if candidate.exists():
                    return candidate
            # Default to input if not found
            return workspace_path / "input" / filename
        else:
            # Legacy: use as absolute/relative path
            return Path(filename)

    def _resolve_write_path(
        self,
        filename: str,
        workspace_path: Optional[Path],
        subdir: str = "output"
    ) -> Path:
        """Resolve path for writing within workspace."""
        if workspace_path:
            if subdir not in ("input", "output", "temp"):
                subdir = "output"
            target = workspace_path / subdir / filename

            # Security: ensure path doesn't escape workspace
            try:
                target.resolve().relative_to(workspace_path.resolve())
            except ValueError:
                raise ValueError(f"Path '{filename}' escapes workspace bounds")

            # Create parent directories if needed
            target.parent.mkdir(parents=True, exist_ok=True)
            return target
        else:
            # Legacy: use as absolute/relative path
            return Path(filename)

    def _read_file(
        self,
        filename: str,
        workspace_path: Optional[Path]
    ) -> Dict:
        """Read file from workspace."""
        path = self._resolve_read_path(filename, workspace_path)
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        return {"success": True, "content": content, "path": str(path)}

    def _write_file(
        self,
        filename: str,
        content: str,
        workspace_path: Optional[Path],
        subdir: str = "output"
    ) -> Dict:
        """Write file to workspace."""
        path = self._resolve_write_path(filename, workspace_path, subdir)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return {"success": True, "message": f"Written to {path}", "path": str(path)}

    def _list_directory(
        self,
        dirname: str,
        workspace_path: Optional[Path],
        subdir: str = "output"
    ) -> Dict:
        """List directory contents within workspace."""
        if workspace_path:
            if subdir not in ("input", "output", "temp"):
                subdir = "output"
            path = workspace_path / subdir / dirname if dirname != "." else workspace_path / subdir
        else:
            path = Path(dirname)

        if not path.exists():
            return {"success": False, "error": f"Directory not found: {path}"}

        items = list(path.iterdir())
        return {
            "success": True,
            "items": [item.name for item in items],
            "path": str(path)
        }

    def _delete_file(
        self,
        filename: str,
        workspace_path: Optional[Path],
        subdir: str = "output"
    ) -> Dict:
        """Delete file from workspace."""
        path = self._resolve_write_path(filename, workspace_path, subdir)
        if not path.exists():
            return {"success": False, "error": f"File not found: {path}"}
        os.remove(path)
        return {"success": True, "message": f"Deleted {path}"}

    def _check_exists(
        self,
        filename: str,
        workspace_path: Optional[Path]
    ) -> Dict:
        """Check if file exists in workspace."""
        if workspace_path:
            # Search all subdirs
            for subdir in ["input", "output", "temp"]:
                candidate = workspace_path / subdir / filename
                if candidate.exists():
                    return {"success": True, "exists": True, "path": str(candidate)}
            return {"success": True, "exists": False}
        else:
            exists = Path(filename).exists()
            return {"success": True, "exists": exists}
# tools/file_system.py
import os
from core.tool_manager import register_tool
from typing import List

WORKSPACE_DIR = "workspace"

def _resolve_path(path: str) -> str:
    """Resolves a path to be safely within the workspace directory."""
    # Prevent path traversal attacks
    abs_path = os.path.abspath(os.path.join(WORKSPACE_DIR, path))
    if not abs_path.startswith(os.path.abspath(WORKSPACE_DIR)):
        raise ValueError("Error: Path is outside the allowed workspace directory.")
    return abs_path

@register_tool
def read_file(path: str) -> str:
    """
    Reads the content of a file in the workspace.

    Args:
        path: The relative path to the file within the workspace.
    
    Returns:
        The content of the file.
    """
    try:
        safe_path = _resolve_path(path)
        with open(safe_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {e}"

@register_tool
def write_file(path: str, content: str) -> str:
    """
    Writes content to a file in the workspace. Creates directories if they don't exist.

    Args:
        path: The relative path to the file within the workspace.
        content: The content to write to the file.
    
    Returns:
        A success message or an error.
    """
    try:
        safe_path = _resolve_path(path)
        # Ensure parent directory exists
        os.makedirs(os.path.dirname(safe_path), exist_ok=True)
        with open(safe_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"File '{path}' written successfully."
    except Exception as e:
        return f"Error writing file: {e}"

@register_tool
def list_files(path: str = ".") -> List[str]:
    """
    Lists all files and directories in a given path within the workspace.

    Args:
        path: The relative path within the workspace. Defaults to the workspace root.
    
    Returns:
        A list of file and directory names.
    """
    try:
        safe_path = _resolve_path(path)
        return os.listdir(safe_path)
    except Exception as e:
        return [f"Error listing files: {e}"]

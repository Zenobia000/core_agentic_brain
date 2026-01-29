"""
工具函數 - 消除特殊情況
Linus: "Good code has no special cases"
"""

from typing import Any, Dict


def get_config_value(config: Dict[str, Any], *keys) -> Any:
    """統一的 config 訪問，沒有特殊情況

    Args:
        config: 配置字典
        *keys: 鍵路徑

    Returns:
        找到的值或空字典

    Example:
        get_config_value(config, "core", "llm", "model")
    """
    result = config
    for key in keys:
        if isinstance(result, dict):
            result = result.get(key, {})
        else:
            return {}
    return result


def get_nested_config(config: Dict[str, Any], path: str) -> Any:
    """用點分路徑訪問 config

    Args:
        config: 配置字典
        path: 點分路徑 (e.g., "core.llm.model")

    Returns:
        找到的值或空字典
    """
    return get_config_value(config, *path.split('.'))


def merge_config(base: Dict[str, Any], overlay: Dict[str, Any]) -> Dict[str, Any]:
    """合併配置，overlay 優先

    不用遞歸，不要複雜化
    """
    result = base.copy()
    result.update(overlay)
    return result
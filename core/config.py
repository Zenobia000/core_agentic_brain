"""
配置管理 - 極簡實作 (< 50 行)
載入和合併配置
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional


def load_config(config_path: Optional[Any] = None) -> Dict[str, Any]:
    """載入配置檔案

    Args:
        config_path: 配置檔案路徑，可以是字串或 Path 物件

    Returns:
        配置字典
    """
    # 預設配置
    default_config = {
        "mode": "minimal",
        "core": {
            "llm": {
                "provider": "openai",
                "model": "gpt-3.5-turbo",
                "temperature": 0.7,
                "max_tokens": 2000
            },
            "tools": {
                "enabled": ["python", "files"]
            }
        }
    }

    # 處理路徑參數
    if config_path is None or config_path == "config.yaml":
        config_path = Path("config.yaml")
    elif isinstance(config_path, str):
        config_path = Path(config_path)

    # 載入用戶配置
    user_config = {}
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                user_config = yaml.safe_load(f) or {}
        except Exception as e:
            print(f"Warning: Error reading config file: {e}")

    # 合併配置（用戶配置優先）
    config = merge_configs(default_config, user_config)

    # 從環境變量載入 API key
    if api_key := os.getenv("OPENAI_API_KEY"):
        config.setdefault("core", {}).setdefault("llm", {})["api_key"] = api_key

    return config


def merge_configs(default: Dict, user: Dict) -> Dict:
    """遞迴合併配置字典"""
    result = default.copy()

    for key, value in user.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_configs(result[key], value)
        else:
            result[key] = value

    return result


# 全局配置快取（向後相容）
_config: Dict[str, Any] = {}


def get_config() -> Dict[str, Any]:
    """向後相容的配置獲取函數"""
    global _config
    if not _config:
        _config = load_config()
    return _config

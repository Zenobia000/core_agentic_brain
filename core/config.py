"""
配置管理 - 極簡實作
載入配置並處理環境變數
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
        "version": "2.0",
        "mode": "standard",
        "llm": {
            "provider": "openai",
            "model": "gpt-3.5-turbo",
            "temperature": 0.7,
            "max_tokens": 2000
        },
        "tools": {
            "enabled": ["python", "files"]
        },
        "routing": {
            "enabled": True
        },
        "react": {
            "max_steps": 10,
            "token_budget": 15000,  # Summarization threshold (NOT a hard limit)
            "token_warning_threshold": 0.8,
            "max_consecutive_errors": 3,
            "repetition_window": 5,
            "enable_summarization": True
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

    # 載入 API keys（支援多種 provider）
    config = load_api_keys(config)

    # 向後相容：將 llm 配置複製到 core.llm
    if "llm" in config and "core" not in config:
        config["core"] = {"llm": config["llm"], "tools": config.get("tools", {})}

    return config


def load_api_keys(config: Dict[str, Any]) -> Dict[str, Any]:
    """從環境變數載入 API keys

    支援的環境變數：
    - OPENAI_API_KEY
    - ANTHROPIC_API_KEY
    - GOOGLE_API_KEY
    - AZURE_OPENAI_API_KEY
    - AZURE_OPENAI_ENDPOINT
    """
    provider = config.get("llm", {}).get("provider", "openai")

    # 根據 provider 載入對應的 API key
    api_key_mapping = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "google": "GOOGLE_API_KEY",
        "azure": "AZURE_OPENAI_API_KEY",
        "ollama": None  # Ollama 不需要 API key
    }

    env_var = api_key_mapping.get(provider)
    if env_var and (api_key := os.getenv(env_var)):
        config.setdefault("llm", {})["api_key"] = api_key

    # Azure 特殊處理
    if provider == "azure":
        if endpoint := os.getenv("AZURE_OPENAI_ENDPOINT"):
            config.setdefault("llm", {})["base_url"] = endpoint
        if deployment := os.getenv("AZURE_OPENAI_DEPLOYMENT"):
            config.setdefault("llm", {})["deployment_id"] = deployment

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

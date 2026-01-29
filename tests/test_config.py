#!/usr/bin/env python3
"""
測試新的配置系統
測試多 provider 支援
"""

import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from core.config import load_config
from core.llm import LLMProvider

def test_config_loading():
    """測試配置載入"""
    print("=" * 60)
    print("🧪 測試配置系統")
    print("=" * 60)

    # 載入配置
    config = load_config()

    print("\n📋 載入的配置:")
    print(f"  Version: {config.get('version')}")
    print(f"  Mode: {config.get('mode')}")
    print(f"  LLM Provider: {config.get('llm', {}).get('provider')}")
    print(f"  LLM Model: {config.get('llm', {}).get('model')}")
    print(f"  Tools: {config.get('tools', {}).get('enabled')}")

    # 檢查環境變數
    print("\n🔑 環境變數檢查:")
    env_vars = [
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "GOOGLE_API_KEY",
        "AZURE_OPENAI_API_KEY"
    ]

    for var in env_vars:
        value = os.getenv(var)
        if value:
            print(f"  ✓ {var}: {'***' + value[-4:] if len(value) > 4 else '***'}")
        else:
            print(f"  ✗ {var}: 未設定")

    return config


def test_llm_providers():
    """測試 LLM Provider"""
    print("\n" + "=" * 60)
    print("🤖 測試 LLM Provider")
    print("=" * 60)

    # 測試配置
    test_configs = [
        {
            "name": "OpenAI",
            "config": {
                "provider": "openai",
                "model": "gpt-3.5-turbo",
                "temperature": 0.7,
                "max_tokens": 100
            }
        },
        {
            "name": "Anthropic",
            "config": {
                "provider": "anthropic",
                "model": "claude-3-haiku-20240307",
                "temperature": 0.5,
                "max_tokens": 100
            }
        },
        {
            "name": "Google",
            "config": {
                "provider": "google",
                "model": "gemini-2.0-flash-exp",
                "temperature": 0.7,
                "max_tokens": 100
            }
        },
        {
            "name": "Ollama",
            "config": {
                "provider": "ollama",
                "model": "llama3.2",
                "temperature": 0.7,
                "max_tokens": 100
            }
        }
    ]

    for test in test_configs:
        print(f"\n📝 測試 {test['name']}:")
        try:
            provider = LLMProvider(test['config'])
            print(f"  ✓ 初始化成功")
            print(f"    Provider: {provider.provider}")
            print(f"    Model: {provider.model}")
        except Exception as e:
            print(f"  ✗ 初始化失敗: {e}")


def test_backward_compatibility():
    """測試向後相容性"""
    print("\n" + "=" * 60)
    print("🔄 測試向後相容性")
    print("=" * 60)

    # 測試舊式配置格式
    old_config = {
        "core": {
            "llm": {
                "provider": "openai",
                "model": "gpt-3.5-turbo"
            }
        }
    }

    # 載入配置
    from core.config import load_api_keys
    config = load_api_keys(old_config)

    print("✓ 舊式 core.llm 配置格式支援")

    # 測試別名
    from core.llm import LLMWrapper, LLMClient

    print("✓ LLMWrapper 別名支援")
    print("✓ LLMClient 別名支援")


def main():
    """主測試函數"""
    try:
        # 測試配置載入
        config = test_config_loading()

        # 測試 LLM Provider
        test_llm_providers()

        # 測試向後相容性
        test_backward_compatibility()

        print("\n" + "=" * 60)
        print("✅ 所有測試完成！")
        print("=" * 60)
        print("\nLinus 會說：")
        print('"Good defaults work. Most users won\'t need to change anything."')

    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
#!/usr/bin/env python3
"""
Core Agentic Brain - 統一入口 (< 50 行)
極簡的 AI Agent 平台
"""

import sys
import asyncio
from pathlib import Path
from core.agent import Agent
from core.config import load_config


def main():
    """主函數 - CLI 模式"""
    # 載入配置
    config_path = Path("config.yaml")
    config = load_config(config_path) if config_path.exists() else {}

    # 初始化 Agent
    try:
        agent = Agent(config)
    except Exception as e:
        print(f"Error initializing agent: {e}")
        print("Please check your configuration and API keys.")
        return 1

    # 顯示歡迎訊息
    print("Core Agentic Brain - Minimal Mode")
    print("Type 'exit' to quit, 'reset' to clear history\n")

    # 互動循環
    while True:
        try:
            # 獲取用戶輸入
            user_input = input("You: ").strip()

            # 特殊命令
            if user_input.lower() in ['exit', 'quit', 'q']:
                print("Goodbye!")
                break
            elif user_input.lower() == 'reset':
                agent.reset()
                print("Conversation history cleared.\n")
                continue
            elif not user_input:
                continue

            # 處理用戶輸入
            print("AI: ", end="", flush=True)
            response = agent.run(user_input)  # 使用同步介面
            print(response + "\n")

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())

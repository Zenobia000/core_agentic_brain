#!/usr/bin/env python3
"""
Core Agentic Brain - 主程式入口
基於 Kernel 中央調度架構
"""

import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# 添加專案路徑
sys.path.insert(0, str(Path(__file__).parent))

from core.kernel import Kernel
from core.types import TaskContext


async def interactive_mode(kernel: Kernel):
    """互動模式 - CLI 介面"""
    print("\n" + "=" * 60)
    print("🧠 Core Agentic Brain - Interactive Mode")
    print("基於 Linus 原則：簡單、直接、無特殊情況")
    print("=" * 60)
    print("\n指令:")
    print("  - 輸入任務或問題")
    print("  - 輸入 'exit' 或 'quit' 退出")
    print("  - 輸入 'test' 執行測試")
    print("  - 輸入 'clear' 或 'cls' 清除畫面")
    print("  - 輸入 'help' 顯示幫助")
    print()

    while True:
        try:
            # 獲取用戶輸入
            user_input = input(">>> ").strip()

            # 檢查退出指令
            if user_input.lower() in ['exit', 'quit', 'q']:
                print("\n👋 再見！")
                break

            # 檢查幫助指令
            if user_input.lower() == 'help':
                print("\n可用功能:")
                print("  • 自然語言處理：直接輸入問題或任務")
                print("  • Python 執行：要求執行 Python 代碼")
                print("  • 檔案操作：要求讀寫檔案")
                print("  • 測試系統：輸入 'test'")
                print("  • 清除畫面：輸入 'clear' 或 'cls'")
                print()
                continue

            # 檢查測試指令
            if user_input.lower() == 'test':
                print("\n執行快速測試...")
                result = await kernel.call_tool("python", {
                    "code": "print('System is working!')"
                })
                print(f"測試結果: {result}")
                continue

            # 檢查清除畫面指令
            if user_input.lower() in ['clear', 'cls']:
                # 跨平台清除終端：Windows 用 cls，Unix/Linux/Mac 用 clear
                os.system('cls' if os.name == 'nt' else 'clear')
                continue

            # 空輸入
            if not user_input:
                continue

            # 處理任務
            print(f"\n🔄 處理中...")
            result = await kernel.execute(user_input)

            # 顯示結果
            if result.success:
                print(f"\n✅ 完成:")
                if result.response:
                    print(result.response)
            else:
                print(f"\n❌ 錯誤:")
                print(result.error or "未知錯誤")

            # 顯示元資料（如果有）
            if result.metadata:
                print(f"\n📊 元資料:")
                for key, value in result.metadata.items():
                    print(f"  • {key}: {value}")

        except KeyboardInterrupt:
            print("\n\n⚠️  使用 'exit' 正常退出")
            continue
        except Exception as e:
            print(f"\n❌ 發生錯誤: {e}")
            continue


async def batch_mode(kernel: Kernel, task: str):
    """批次模式 - 執行單個任務"""
    print(f"\n🔄 執行任務: {task}")

    try:
        result = await kernel.execute(task)

        if result.success:
            print(f"\n✅ 成功:")
            print(result.response)
            return 0
        else:
            print(f"\n❌ 失敗:")
            print(result.error or "未知錯誤")
            return 1

    except Exception as e:
        print(f"\n❌ 錯誤: {e}")
        return 1


async def main():
    """主函數"""
    # 初始化 Kernel
    try:
        kernel = Kernel()
    except Exception as e:
        print(f"❌ 無法初始化系統: {e}")
        print("\n請檢查:")
        print("  1. 是否設置了 OPENAI_API_KEY")
        print("  2. 是否安裝了所有依賴")
        print("  3. 是否在正確的目錄")
        return 1

    # 檢查命令行參數
    if len(sys.argv) > 1:
        # 批次模式
        task = " ".join(sys.argv[1:])
        return await batch_mode(kernel, task)
    else:
        # 互動模式
        await interactive_mode(kernel)
        return 0


if __name__ == "__main__":
    # 運行主程式
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n👋 程式被中斷")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 致命錯誤: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
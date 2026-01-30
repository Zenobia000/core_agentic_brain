#!/usr/bin/env python3
"""
Core Agentic Brain - 主程式入口
基於 Kernel 中央調度架構
"""

import os
import sys
import asyncio
import uuid
from pathlib import Path
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# 添加專案路徑
sys.path.insert(0, str(Path(__file__).parent))

from core.kernel import Kernel
from core.types import TaskContext
from core.memory import ConversationMemory, MemoryManager


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
    print("  - 輸入 'memory' 顯示記憶體狀態")
    print("  - 輸入 'reset' 重置對話歷史")
    print("  - 輸入 'help' 顯示幫助")
    print()

    # Initialize session memory for conversation history
    session_memory = MemoryManager.from_config(kernel.config)

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
                print("  • 記憶體狀態：輸入 'memory'")
                print("  • 重置歷史：輸入 'reset'")
                print()
                continue

            # 檢查記憶體狀態指令
            if user_input.lower() == 'memory':
                stats = session_memory.get_stats()
                print(f"\n📊 記憶體狀態:")
                print(f"  • 當前訊息數: {stats['current_messages']}")
                print(f"  • 總處理訊息: {stats['total_processed']}")
                print(f"  • 壓縮次數: {stats['compaction_count']}")
                print(f"  • 窗口大小: {stats['window_size']}")
                print(f"  • 策略: {stats['strategy']}")
                print()
                continue

            # 檢查重置歷史指令
            if user_input.lower() == 'reset':
                session_memory.clear(keep_system=False)
                print("\n🔄 對話歷史已重置")
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

            # Generate run_id once for this conversation turn
            # Clarifications will reuse the same run_id
            run_id = f"run_{uuid.uuid4().hex[:8]}"

            # Create context with conversation history and run_id
            context = TaskContext(
                prompt=user_input,
                run_id=run_id,
                messages=session_memory.to_context_messages()
            )

            result = await kernel.execute(user_input, context)

            # 處理 Clarification Gate - 使用 while 循環處理多次澄清
            # Note: All clarifications share the same run_id (same workspace)
            current_input = user_input
            clarification_count = 0
            max_clarifications = 3  # 防止無限循環

            while result.error == "CLARIFICATION_NEEDED" and clarification_count < max_clarifications:
                clarification_count += 1
                key_questions = result.metadata.get("key_questions", [])
                print(f"\n🤔 需要更多資訊 ({clarification_count}/{max_clarifications}):")
                for i, q in enumerate(key_questions, 1):
                    print(f"  {i}. {q}")
                print()

                # 讓用戶輸入補充資訊
                clarification = input("請補充說明 (或輸入 'skip' 跳過): ").strip()

                if clarification.lower() == 'skip':
                    # 強制跳過 Gate，繼續執行 (reuse same run_id)
                    print(f"\n🔄 跳過澄清，嘗試執行...")
                    context = TaskContext(
                        prompt=current_input,
                        run_id=run_id,  # Reuse run_id
                        messages=session_memory.to_context_messages(),
                        metadata={"clarification_provided": True, "skip_clarification": True}
                    )
                    result = await kernel.execute(current_input, context)
                    break
                elif clarification:
                    # 合併原始請求與補充資訊，重新執行 (reuse same run_id)
                    current_input = f"{current_input}\n\n補充資訊: {clarification}"
                    print(f"\n🔄 重新處理中...")

                    # Mark that clarification was provided to skip Gate
                    context = TaskContext(
                        prompt=current_input,
                        run_id=run_id,  # Reuse run_id
                        messages=session_memory.to_context_messages(),
                        metadata={"clarification_provided": True}
                    )
                    result = await kernel.execute(current_input, context)
                else:
                    print("未提供補充資訊，任務取消。")
                    break

            # 如果超過最大澄清次數
            if result.error == "CLARIFICATION_NEEDED" and clarification_count >= max_clarifications:
                print(f"\n⚠️ 已達最大澄清次數 ({max_clarifications})，任務取消。")
                continue

            # 顯示結果
            if result.success:
                # Check for max_steps warning (only remaining termination concern)
                termination_reason = None
                if result.metadata:
                    exec_chain = result.metadata.get("execution_chain", [])
                    for step in exec_chain:
                        if step.get("agent") == "executor" and "termination_reason" in step:
                            termination_reason = step.get("termination_reason")
                            break

                if termination_reason == "max_steps":
                    print(f"\n⚠️  警告: 達到最大執行步數，任務可能未完成")
                    print(f"   提示: 可以縮小任務範圍或在 config.yaml 增加 max_steps\n")

                print(f"\n✅ 完成:")
                if result.response:
                    print(result.response)

                # Save successful conversation to memory
                session_memory.add("user", user_input)
                session_memory.add("assistant", result.response or "")
            else:
                print(f"\n❌ 錯誤:")
                print(result.error or "未知錯誤")

            # 顯示元資料（如果有）
            if result.metadata:
                print(f"\n📊 元資料:")
                for key, value in result.metadata.items():
                    print(f"  • {key}: {value}")

            # Show memory stats if compaction occurred
            stats = session_memory.get_stats()
            if stats["compaction_count"] > 0 and stats["current_messages"] > 0:
                print(f"\n💾 記憶: {stats['current_messages']} 訊息, {stats['compaction_count']} 次壓縮")

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
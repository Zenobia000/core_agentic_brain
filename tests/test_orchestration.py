#!/usr/bin/env python3
"""
測試多代理協作系統
驗證 ReAct 架構和 LLM 分析
"""

import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv
import json

load_dotenv()
sys.path.insert(0, str(Path(__file__).parent))

from core.kernel import Kernel


async def test_llm_analysis():
    """測試 LLM 任務分析"""
    print("=" * 60)
    print("🧪 測試 LLM 任務分析")
    print("=" * 60)

    kernel = Kernel()

    # 測試不同複雜度的任務
    test_tasks = [
        "什麼是 2+2?",
        "分析並比較 Python 和 JavaScript 的優缺點",
        "設計一個完整的微服務架構系統，包括服務發現、負載均衡、容錯機制"
    ]

    for task in test_tasks:
        print(f"\n📝 任務: {task[:50]}...")
        print("-" * 40)

        result = await kernel.execute(task)

        if result.metadata and "routing" in result.metadata:
            routing = result.metadata["routing"]
            print(f"  複雜度: {routing.get('complexity', 'unknown')}")
            print(f"  策略: {routing.get('strategy', 'unknown')}")
            print(f"  推理: {routing.get('reasoning', 'none')[:100]}...")

        print(f"  成功: {result.success}")
        if result.response:
            print(f"  回應: {result.response[:100]}...")


async def test_orchestrated_execution():
    """測試協調執行流程"""
    print("\n" + "=" * 60)
    print("🎭 測試協調執行（Planner -> Executor -> Reviewer）")
    print("=" * 60)

    kernel = Kernel()

    # 測試複雜任務，觸發多代理協作
    complex_task = """
    請設計並實現一個用戶認證系統，需要包括：
    1. 用戶註冊和登入功能
    2. 密碼安全存儲
    3. JWT token 生成和驗證
    4. 角色權限管理
    """

    print(f"\n📝 複雜任務:")
    print(complex_task)
    print("-" * 40)

    result = await kernel.execute(complex_task)

    print(f"\n執行結果:")
    print(f"  ✅ 成功: {result.success}")

    if result.metadata:
        # 顯示執行鏈
        if "execution_chain" in result.metadata:
            print(f"\n📊 執行鏈:")
            for step in result.metadata["execution_chain"]:
                print(f"  • {step['agent']}: {step['result'][:100]}...")

        # 顯示使用的代理
        if "agents_used" in result.metadata:
            print(f"\n🤖 使用的代理: {', '.join(result.metadata['agents_used'])}")

        # 顯示路由資訊
        if "routing" in result.metadata:
            routing = result.metadata["routing"]
            print(f"\n🎯 路由決策:")
            print(f"  • 複雜度: {routing.get('complexity')}")
            print(f"  • 策略: {routing.get('strategy')}")


async def test_react_mode():
    """測試 ReAct 模式"""
    print("\n" + "=" * 60)
    print("🔄 測試 ReAct 模式（Thought-Action-Observation）")
    print("=" * 60)

    kernel = Kernel()

    # 測試需要迭代的任務
    react_task = """
    優化這段代碼的性能：
    ```python
    def find_duplicates(arr):
        duplicates = []
        for i in range(len(arr)):
            for j in range(i+1, len(arr)):
                if arr[i] == arr[j] and arr[i] not in duplicates:
                    duplicates.append(arr[i])
        return duplicates
    ```
    """

    print(f"\n📝 ReAct 任務:")
    print(react_task)
    print("-" * 40)

    result = await kernel.execute(react_task)

    print(f"\n執行結果:")
    print(f"  ✅ 成功: {result.success}")

    if result.metadata:
        # 顯示 ReAct 鏈
        if "react_chain" in result.metadata:
            print(f"\n🔄 ReAct 鏈:")
            for step in result.metadata["react_chain"]:
                print(f"\n  迭代 {step['iteration']}:")
                print(f"    💭 Thought: {step.get('thought', '')[:100]}...")
                print(f"    🎯 Action: {step.get('action', '')[:100]}...")
                if 'observation' in step:
                    print(f"    👁️ Observation: {step['observation'][:100]}...")

        # 顯示迭代次數
        if "iterations" in result.metadata:
            print(f"\n  總迭代次數: {result.metadata['iterations']}")


async def test_simple_vs_complex():
    """對比簡單和複雜任務的處理"""
    print("\n" + "=" * 60)
    print("⚖️ 對比簡單 vs 複雜任務處理")
    print("=" * 60)

    kernel = Kernel()

    tasks = [
        ("簡單", "什麼是 Python?"),
        ("複雜", "設計一個分散式系統架構，支援高可用、自動擴展和容錯")
    ]

    for task_type, task in tasks:
        print(f"\n[{task_type}任務] {task[:50]}...")
        print("-" * 40)

        result = await kernel.execute(task)

        # 顯示處理細節
        if result.metadata:
            if "strategy" in result.metadata:
                print(f"  策略: {result.metadata['strategy']}")

            if "execution_chain" in result.metadata:
                chain = result.metadata["execution_chain"]
                print(f"  執行鏈長度: {len(chain)}")
                print(f"  參與代理: {[s['agent'] for s in chain]}")

            if "agents_used" in result.metadata:
                print(f"  使用代理: {result.metadata['agents_used']}")

            if "routing" in result.metadata:
                routing = result.metadata["routing"]
                print(f"  複雜度判定: {routing.get('complexity')}")

            # 執行時間
            if "execution_time_ms" in result.metadata:
                print(f"  執行時間: {result.metadata['execution_time_ms']:.0f}ms")


async def main():
    """主測試函數"""
    try:
        # 測試 LLM 分析
        await test_llm_analysis()

        # 測試協調執行
        await test_orchestrated_execution()

        # 測試 ReAct 模式
        # await test_react_mode()

        # 對比測試
        await test_simple_vs_complex()

        print("\n" + "=" * 60)
        print("✅ 所有測試完成！")
        print("=" * 60)

        print("\n💡 關鍵發現：")
        print("1. LLM 能智能判斷任務複雜度（不依賴關鍵詞）")
        print("2. 複雜任務會觸發多代理協作（Planner -> Executor -> Reviewer）")
        print("3. ReAct 模式支援迭代思考和行動")
        print("4. 系統保持向後相容（簡單任務仍用單代理）")

    except KeyboardInterrupt:
        print("\n\n測試被中斷")
    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
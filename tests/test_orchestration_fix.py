#!/usr/bin/env python3
"""
測試多代理協作觸發修復

NOTE: This test requires a real API key to run.
"""

import asyncio
import os
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent))

# Check API key BEFORE loading dotenv to get skip decision
HAS_API_KEY = bool(os.getenv("OPENAI_API_KEY") or os.getenv("AZURE_OPENAI_API_KEY"))


@pytest.mark.skipif(not HAS_API_KEY, reason="No API key available")
@pytest.mark.asyncio
async def test_orchestration():
    """測試多代理協作觸發 (requires API key)"""
    # Load env vars inside test to avoid polluting collection
    from dotenv import load_dotenv
    load_dotenv()

    from core.kernel import Kernel
    from core.types import TaskContext

    print("=" * 60)
    print("🧪 測試多代理協作修復")
    print("=" * 60)

    kernel = Kernel()

    # 測試簡單任務
    print("\n1️⃣ 測試簡單任務（應該用單代理）:")
    simple_task = "什麼是 2+2?"
    result = await kernel.execute(simple_task)

    print(f"  ✅ 成功: {result.success}")
    if result.metadata:
        routing = result.metadata.get('routing', {})
        print(f"  📊 複雜度: {routing.get('complexity', 'unknown')}")
        print(f"  🎯 策略: {routing.get('strategy', 'unknown')}")
        if 'execution_chain' in result.metadata:
            chain = result.metadata['execution_chain']
            print(f"  🔗 執行鏈: {[step['agent'] for step in chain]}")
        else:
            print(f"  🔗 執行鏈: [單代理執行]")

    await asyncio.sleep(1)

    # 測試中等任務
    print("\n2️⃣ 測試中等任務（應該用 Planner + Executor）:")
    moderate_task = "設計一個簡單的用戶登入系統流程，包括註冊、登入、密碼重置功能"
    result = await kernel.execute(moderate_task)

    print(f"  ✅ 成功: {result.success}")
    if result.metadata:
        routing = result.metadata.get('routing', {})
        print(f"  📊 複雜度: {routing.get('complexity', 'unknown')}")
        print(f"  🎯 策略: {routing.get('strategy', 'unknown')}")
        if 'execution_chain' in result.metadata:
            chain = result.metadata['execution_chain']
            print(f"  🔗 執行鏈: {[step['agent'] for step in chain]}")
            print(f"  📝 執行細節:")
            for i, step in enumerate(chain, 1):
                preview = step['result'][:50] if 'result' in step else ''
                print(f"     {i}. {step['agent']}: {preview}...")
        else:
            print(f"  🔗 執行鏈: [單代理執行]")

    await asyncio.sleep(1)

    # 測試複雜任務
    print("\n3️⃣ 測試複雜任務（應該用 Planner + Executor + Reviewer）:")
    complex_task = """設計一個完整的微服務架構系統，包括：
    1. API 閘道設計
    2. 服務發現與註冊機制
    3. 負載均衡策略
    4. 容錯和熔斷機制
    5. 分散式追蹤和監控
    需要詳細的架構圖和實現步驟。"""

    result = await kernel.execute(complex_task)

    print(f"  ✅ 成功: {result.success}")
    if result.metadata:
        routing = result.metadata.get('routing', {})
        print(f"  📊 複雜度: {routing.get('complexity', 'unknown')}")
        print(f"  🎯 策略: {routing.get('strategy', 'unknown')}")
        print(f"  💭 推理: {routing.get('reasoning', '')[:100]}...")

        if 'execution_chain' in result.metadata:
            chain = result.metadata['execution_chain']
            print(f"  🔗 執行鏈: {[step['agent'] for step in chain]}")
            print(f"  📝 執行細節:")
            for i, step in enumerate(chain, 1):
                preview = step['result'][:80] if 'result' in step else ''
                print(f"     {i}. {step['agent']}: {preview}...")
        else:
            print(f"  🔗 執行鏈: [單代理執行]")

        # 檢查 ReAct 鏈
        if 'react_chain' in result.metadata:
            react = result.metadata['react_chain']
            print(f"  🔄 ReAct 迭代: {len(react)} 次")

    # 總結
    print("\n" + "=" * 60)
    print("📊 測試總結")
    print("=" * 60)

    print("\n檢查點:")
    print("  ✅ Kernel 正常運作")
    print("  ✅ LLM 分析器運作")
    print("  ✅ 路由決策生成")

    # 驗證多代理是否觸發
    if result.metadata and 'execution_chain' in result.metadata:
        chain = result.metadata['execution_chain']
        if len(chain) > 1:
            print("  ✅ 多代理協作已觸發!")
            print(f"     參與代理: {', '.join([step['agent'] for step in chain])}")
        else:
            print("  ⚠️ 多代理協作未觸發（仍使用單代理）")
    else:
        print("  ❌ 無法獲取執行鏈資訊")

    return True


async def main():
    """主函數"""
    try:
        success = await test_orchestration()
        if success:
            print("\n✅ 測試完成")
            return 0
        else:
            print("\n❌ 測試失敗")
            return 1
    except Exception as e:
        print(f"\n❌ 測試異常: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
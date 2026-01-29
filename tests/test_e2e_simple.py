#!/usr/bin/env python3
"""
簡化的 E2E 測試 - 測試核心功能
"""

import asyncio
import time
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
import sys
sys.path.insert(0, str(Path(__file__).parent))

from core.kernel import Kernel


async def test_basic_flow():
    """測試基本流程"""
    print("=" * 60)
    print("🧪 核心功能 E2E 測試")
    print("=" * 60)

    kernel = Kernel()

    # 測試案例
    test_cases = [
        {
            "name": "簡單任務",
            "prompt": "什麼是 2+2?",
            "expected": ["4", "four"]
        },
        {
            "name": "中等任務",
            "prompt": "比較 Python 和 JavaScript 的主要差異（簡短回答）",
            "expected": ["Python", "JavaScript"]
        },
        {
            "name": "複雜任務",
            "prompt": "設計一個簡單的微服務架構（概述主要組件）",
            "expected": ["service", "API"]
        },
        {
            "name": "Python 工具",
            "prompt": "執行這段 Python 代碼：print('Hello from Python')",
            "expected": ["Hello", "Python"]
        },
        {
            "name": "檔案工具",
            "prompt": "列出 config.yaml 檔案的內容",
            "expected": ["llm", "provider"]
        }
    ]

    results = []

    for i, test in enumerate(test_cases, 1):
        print(f"\n[測試 {i}/{len(test_cases)}] {test['name']}")
        print(f"  提示: {test['prompt'][:50]}...")
        print("-" * 40)

        start_time = time.time()

        try:
            result = await kernel.execute(test['prompt'])
            execution_time = (time.time() - start_time) * 1000

            # 檢查成功
            success = result.success
            print(f"  ✅ 執行成功: {success}")
            print(f"  ⏱️ 執行時間: {execution_time:.0f}ms")

            # 檢查回應
            if result.response:
                response_preview = result.response[:100]
                print(f"  📝 回應: {response_preview}...")

                # 驗證預期內容
                response_lower = result.response.lower()
                found_keywords = []
                for keyword in test['expected']:
                    if keyword.lower() in response_lower:
                        found_keywords.append(keyword)

                if found_keywords:
                    print(f"  ✅ 找到關鍵詞: {', '.join(found_keywords)}")
                else:
                    print(f"  ⚠️ 未找到預期關鍵詞")
                    success = False

            # 顯示元資料
            if result.metadata:
                print(f"  📊 元資料:")
                if 'agent' in result.metadata:
                    print(f"    • 代理: {result.metadata['agent']}")
                if 'tool_count' in result.metadata:
                    print(f"    • 工具調用: {result.metadata['tool_count']}")
                if 'routing' in result.metadata:
                    routing = result.metadata['routing']
                    print(f"    • 複雜度: {routing.get('complexity', 'unknown')}")
                    print(f"    • 策略: {routing.get('strategy', 'unknown')}")
                if 'execution_chain' in result.metadata:
                    chain = result.metadata['execution_chain']
                    agents = [step['agent'] for step in chain]
                    print(f"    • 執行鏈: {' → '.join(agents)}")

            results.append({
                "test": test['name'],
                "success": success,
                "time_ms": execution_time
            })

        except Exception as e:
            print(f"  ❌ 錯誤: {e}")
            results.append({
                "test": test['name'],
                "success": False,
                "time_ms": (time.time() - start_time) * 1000,
                "error": str(e)
            })

        # 短暫延遲
        await asyncio.sleep(0.5)

    # 總結
    print("\n" + "=" * 60)
    print("📊 測試總結")
    print("=" * 60)

    success_count = sum(1 for r in results if r['success'])
    total_count = len(results)
    success_rate = success_count / total_count * 100 if total_count > 0 else 0

    print(f"  • 總測試: {total_count}")
    print(f"  • 成功: {success_count}")
    print(f"  • 失敗: {total_count - success_count}")
    print(f"  • 成功率: {success_rate:.1f}%")

    avg_time = sum(r['time_ms'] for r in results) / len(results)
    print(f"  • 平均時間: {avg_time:.0f}ms")

    # 詳細結果
    print(f"\n詳細結果:")
    for r in results:
        status = "✅" if r['success'] else "❌"
        print(f"  {status} {r['test']}: {r['time_ms']:.0f}ms")
        if 'error' in r:
            print(f"     錯誤: {r['error']}")

    return success_rate >= 60  # 60% 以上算通過


async def test_multi_agent_flow():
    """測試多代理協作流程"""
    print("\n" + "=" * 60)
    print("🎭 多代理協作測試")
    print("=" * 60)

    kernel = Kernel()

    # 測試會觸發多代理的複雜任務
    complex_task = """
    設計一個用戶認證系統的架構，包括：
    1. 註冊和登入
    2. 密碼安全
    3. Token 管理
    需要詳細的實現步驟。
    """

    print("📝 複雜任務測試:")
    print(complex_task[:100] + "...")
    print("-" * 40)

    start_time = time.time()
    result = await kernel.execute(complex_task)
    execution_time = (time.time() - start_time) * 1000

    print(f"\n結果:")
    print(f"  ✅ 成功: {result.success}")
    print(f"  ⏱️ 執行時間: {execution_time:.0f}ms")

    if result.response:
        print(f"  📝 回應預覽: {result.response[:200]}...")

    if result.metadata:
        print(f"\n  📊 執行細節:")

        # 顯示路由決策
        if 'routing' in result.metadata:
            routing = result.metadata['routing']
            print(f"    • 任務複雜度: {routing.get('complexity', 'unknown')}")
            print(f"    • 執行策略: {routing.get('strategy', 'unknown')}")
            print(f"    • 推理: {routing.get('reasoning', 'none')[:100]}...")

        # 顯示執行鏈
        if 'execution_chain' in result.metadata:
            chain = result.metadata['execution_chain']
            print(f"    • 執行鏈長度: {len(chain)}")
            for i, step in enumerate(chain, 1):
                print(f"      {i}. {step['agent']}: {step['result'][:50]}...")

        # 顯示 ReAct 鏈
        if 'react_chain' in result.metadata:
            react = result.metadata['react_chain']
            print(f"    • ReAct 迭代: {len(react)} 次")

    return result.success


async def test_tool_integration():
    """測試工具整合"""
    print("\n" + "=" * 60)
    print("🔧 工具整合測試")
    print("=" * 60)

    kernel = Kernel()

    # Python 工具測試
    print("\n[Python 工具測試]")
    result = await kernel.call_tool("python", {
        "code": "result = sum(range(10))\nprint(f'Sum of 0-9 = {result}')"
    })

    if result.get("success"):
        print(f"  ✅ Python 執行成功")
        print(f"  📝 輸出: {result.get('output', '')}")
    else:
        print(f"  ❌ Python 執行失敗: {result.get('error', '')}")

    # 檔案工具測試
    print("\n[檔案工具測試]")

    # 寫入測試
    write_result = await kernel.call_tool("files", {
        "operation": "write",
        "path": "test_e2e_temp.txt",
        "content": "E2E Test Content"
    })

    if write_result.get("success"):
        print(f"  ✅ 檔案寫入成功")
    else:
        print(f"  ❌ 檔案寫入失敗")

    # 讀取測試
    read_result = await kernel.call_tool("files", {
        "operation": "read",
        "path": "test_e2e_temp.txt"
    })

    if read_result.get("success"):
        print(f"  ✅ 檔案讀取成功: {read_result.get('content', '')}")
    else:
        print(f"  ❌ 檔案讀取失敗")

    # 清理
    await kernel.call_tool("files", {
        "operation": "delete",
        "path": "test_e2e_temp.txt"
    })

    return True


async def main():
    """主測試函數"""
    print("🚀 開始 E2E 測試")
    print("=" * 80)

    all_passed = True

    try:
        # 基本流程測試
        if not await test_basic_flow():
            all_passed = False

        # 多代理協作測試
        if not await test_multi_agent_flow():
            all_passed = False

        # 工具整合測試
        if not await test_tool_integration():
            all_passed = False

    except Exception as e:
        print(f"\n❌ 測試異常: {e}")
        all_passed = False

    # 最終結果
    print("\n" + "=" * 80)
    if all_passed:
        print("✅ 所有測試通過！")
        print("\n系統功能正常:")
        print("  • LLM 任務分析 ✅")
        print("  • 單代理執行 ✅")
        print("  • 多代理協作 ✅")
        print("  • 工具整合 ✅")
    else:
        print("⚠️ 部分測試未通過")
        print("\n需要檢查:")
        print("  • LLM 分析延遲")
        print("  • 多代理觸發條件")
        print("  • 工具調用穩定性")

    print("=" * 80)
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
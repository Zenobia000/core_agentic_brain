#!/usr/bin/env python3
"""
測試路由系統 - 驗證不同複雜度任務的處理
"""

import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, str(Path(__file__).parent))

from core.kernel import Kernel


async def test_routing():
    """測試不同複雜度的任務路由"""
    print("=" * 60)
    print("🧪 路由系統測試")
    print("=" * 60)

    # 初始化 Kernel
    kernel = Kernel()

    # 測試案例
    test_cases = [
        {
            "name": "簡單任務",
            "prompts": [
                "你是誰?",
                "什麼是 Python?",
                "列出前 5 個質數",
                "告訴我今天星期幾"
            ]
        },
        {
            "name": "中等任務",
            "prompts": [
                "分析 Python 和 JavaScript 的差異",
                "創建一個簡單的待辦事項應用",
                "計算斐波那契數列的前 20 項",
                "比較不同排序算法的效率"
            ]
        },
        {
            "name": "複雜任務",
            "prompts": [
                "設計一個微服務架構系統",
                "優化這段程式碼的性能: for i in range(n): for j in range(n): print(i*j)",
                "整合 Redis 快取到現有的 REST API",
                "調試這個記憶體洩漏問題"
            ]
        }
    ]

    for category in test_cases:
        print(f"\n### {category['name']} ###")
        print("-" * 40)

        for prompt in category['prompts']:
            print(f"\n📝 任務: {prompt[:50]}...")
            print("-" * 40)

            try:
                result = await kernel.execute(prompt)

                # 顯示路由決策
                if result.metadata:
                    print(f"✅ 完成")
                    if "agent" in result.metadata:
                        print(f"   使用代理: {result.metadata['agent']}")
                    if "execution_time_ms" in result.metadata:
                        print(f"   執行時間: {result.metadata['execution_time_ms']:.0f}ms")
                    if "tool_count" in result.metadata:
                        print(f"   工具調用: {result.metadata['tool_count']} 次")
                else:
                    print(f"✅ 完成（無元資料）")

            except Exception as e:
                print(f"❌ 錯誤: {e}")

    print("\n" + "=" * 60)
    print("測試完成")
    print("=" * 60)


async def test_specific_complex_task():
    """測試特定的複雜任務以驗證 planner 和 reviewer"""
    print("\n" + "=" * 60)
    print("🎯 測試複雜任務路由")
    print("=" * 60)

    kernel = Kernel()

    # 測試會觸發複雜路由的任務
    complex_task = """
    請幫我設計並實現一個完整的用戶認證系統，包括：
    1. 用戶註冊和登入
    2. JWT token 管理
    3. 密碼加密
    4. 角色權限控制
    5. API 端點保護
    """

    print(f"\n📝 複雜任務:\n{complex_task}")
    print("-" * 40)

    result = await kernel.execute(complex_task)

    print(f"\n結果:")
    print(f"✅ 成功: {result.success}")
    if result.response:
        print(f"📄 回應: {result.response[:200]}...")
    if result.metadata:
        print(f"📊 元資料:")
        for key, value in result.metadata.items():
            print(f"   • {key}: {value}")


async def main():
    """主測試函數"""
    try:
        # 基本路由測試
        await test_routing()

        # 複雜任務測試
        await test_specific_complex_task()

    except KeyboardInterrupt:
        print("\n\n測試被中斷")
    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
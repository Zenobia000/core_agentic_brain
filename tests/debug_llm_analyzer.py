#!/usr/bin/env python3
"""
調試 LLM 分析器輸出
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, str(Path(__file__).parent))

from core.kernel import Kernel
from core.types import TaskContext
from router.llm_analyzer import LLMTaskAnalyzer


async def debug_analyzer():
    """調試 LLM 分析器"""
    print("=" * 60)
    print("🔍 調試 LLM 分析器輸出")
    print("=" * 60)

    kernel = Kernel()
    analyzer = LLMTaskAnalyzer(llm_provider=kernel.llm)

    # 測試不同複雜度的任務
    test_cases = [
        {
            "name": "簡單任務",
            "prompt": "什麼是 2+2?"
        },
        {
            "name": "中等任務",
            "prompt": "設計一個簡單的用戶登入系統流程，包括註冊、登入、密碼重置功能"
        },
        {
            "name": "複雜任務",
            "prompt": """設計一個完整的微服務架構系統，包括：
            1. API 閘道設計
            2. 服務發現與註冊機制
            3. 負載均衡策略
            4. 容錯和熔斷機制
            5. 分散式追蹤和監控
            需要詳細的架構圖和實現步驟。"""
        }
    ]

    for test in test_cases:
        print(f"\n📝 測試: {test['name']}")
        print(f"   提示: {test['prompt'][:50]}...")
        print("-" * 50)

        context = TaskContext(prompt=test['prompt'])

        try:
            # 調用 LLM 分析器
            routing = await analyzer.analyze(context)

            print(f"✅ 分析成功")
            print(f"  複雜度: {routing.complexity.value if hasattr(routing, 'complexity') else 'N/A'}")
            print(f"  策略: {routing.strategy if hasattr(routing, 'strategy') else 'N/A'}")

            if hasattr(routing, 'agents') and routing.agents:
                print(f"  代理列表 ({len(routing.agents)} 個):")
                for agent in routing.agents:
                    print(f"    - {agent.value if hasattr(agent, 'value') else agent}")
            else:
                print(f"  代理列表: 無")

            print(f"  推理: {routing.reasoning[:100] if hasattr(routing, 'reasoning') else 'N/A'}...")

            # 檢查元資料
            if hasattr(routing, 'metadata') and routing.metadata:
                print(f"  元資料:")
                if 'llm_analysis' in routing.metadata:
                    analysis = routing.metadata['llm_analysis']
                    print(f"    - LLM 原始分析:")
                    print(f"      complexity: {analysis.get('complexity', 'N/A')}")
                    print(f"      strategy: {analysis.get('strategy', 'N/A')}")
                    print(f"      recommended_agents: {analysis.get('recommended_agents', [])}")

        except Exception as e:
            print(f"❌ 分析失敗: {e}")
            import traceback
            traceback.print_exc()

        await asyncio.sleep(1)

    print("\n" + "=" * 60)
    print("🎯 調試結論")
    print("=" * 60)

    print("\n關鍵問題檢查:")
    print("1. LLM 是否返回多個代理？")
    print("2. 代理類型是否正確（AgentRole 枚舉）？")
    print("3. 複雜度判斷是否準確？")
    print("4. 策略選擇是否合理？")


async def main():
    try:
        await debug_analyzer()
        return 0
    except Exception as e:
        print(f"\n❌ 調試失敗: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
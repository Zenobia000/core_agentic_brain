"""
E2E Test for System 1 (Fast) vs System 2 (Slow) Routing Logic
驗證：
1. 簡單指令是否觸發 System 1 (Fast Path)
2. 複雜指令是否觸發 System 2 (Refined Goal)
3. Planner 是否接收到重塑後的目標

NOTE: These tests require a real API key to run.
"""

import os
import asyncio
import pytest


def _check_api_key():
    """Check for API key at runtime and skip if not found."""
    if not (os.getenv("OPENAI_API_KEY") or os.getenv("AZURE_OPENAI_API_KEY")):
        pytest.skip("No API key available (requires OPENAI_API_KEY or AZURE_OPENAI_API_KEY)")

# 模擬的複雜指令
COMPLEX_PROMPT = """
幫我重構 core/kernel.py，我想把所有同步方法都改成異步，
並且確保所有的 logger 都加上 run_id 上下文。
請先分析依賴關係，不要破壞現有的測試。
"""

# 模擬的簡單指令
SIMPLE_PROMPT = "ls -la"

@pytest.mark.asyncio
async def test_system1_fast_path():
    """驗證 System 1 快速路徑 (requires API key)"""
    _check_api_key()

    from core.kernel import Kernel
    from core.types import TaskContext

    print("\n[Test] System 1 Fast Path")
    kernel = Kernel()
    
    # 模擬簡單任務
    context = TaskContext(prompt=SIMPLE_PROMPT)
    
    # 這裡我們只測試 Router，不需要真的執行 (Mock Kernel 執行流程)
    from router.llm_analyzer import LLMTaskAnalyzer
    analyzer = LLMTaskAnalyzer(llm_provider=kernel.llm)
    
    decision = await analyzer.analyze(context)
    
    print(f"Strategy: {decision.strategy}")
    print(f"Complexity: {decision.complexity}")
    print(f"Reasoning: {decision.reasoning}")
    
    assert decision.complexity.value == "simple"
    assert decision.strategy in ["direct", "react"]
    assert "system_mode" in decision.metadata
    assert decision.metadata["system_mode"] == "system_1"
    print("✅ System 1 Verified")


@pytest.mark.asyncio
async def test_system2_slow_path():
    """驗證 System 2 慢思考路徑 (requires API key)"""
    _check_api_key()

    from core.kernel import Kernel
    from core.types import TaskContext

    print("\n[Test] System 2 Slow Path")
    kernel = Kernel()
    
    # 確保有 LLM 才能測試 System 2
    if not kernel.llm:
        print("⚠️ No LLM configured, skipping System 2 test")
        return

    context = TaskContext(prompt=COMPLEX_PROMPT)
    
    from router.llm_analyzer import LLMTaskAnalyzer
    analyzer = LLMTaskAnalyzer(llm_provider=kernel.llm)
    
    decision = await analyzer.analyze(context)
    
    print(f"Strategy: {decision.strategy}")
    print(f"Complexity: {decision.complexity}")
    print(f"Refined Goal: {decision.metadata.get('refined_goal')[:100]}...")
    
    # 驗證 System 2 特徵
    assert decision.metadata.get("system_mode") == "system_2"
    assert "refined_goal" in decision.metadata
    assert "thought_process" in decision.metadata
    # 確保 refined_goal 與原始 prompt 不同 (經過重塑)
    assert decision.metadata["refined_goal"] != COMPLEX_PROMPT
    
    print("✅ System 2 Verified")

if __name__ == "__main__":
    # 手動執行測試
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(test_system1_fast_path())
        print("-" * 30)
        # 注意：需要配置真實 LLM 才能跑 test_system2_slow_path
        # 這裡僅作代碼示範，實際運行依賴環境配置
        print("Run 'pytest tests/test_system1_2_routing.py' to execute full suite")
    finally:
        loop.close()

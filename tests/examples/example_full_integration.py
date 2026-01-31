#!/usr/bin/env python3
"""
DEPRECATED: 完整整合範例

This example used the old router/executor.py which has been removed.
The routing execution is now handled by:
- core/kernel.py (Kernel) - Main entry point
- core/orchestration.py (MultiAgentOrchestrator) - Agent coordination

For current usage, see:
- tests/integration/test_main_minimal.py
- main.py
"""

import sys
print("WARNING: This example is deprecated. Use Kernel-based architecture.")
print("See: tests/integration/test_main_minimal.py")
sys.exit(0)

import asyncio
from pathlib import Path
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# 核心組件
from core.types import TaskContext, ExecutionResult
from core.prompt_loader import get_prompt_loader
from core.logger import logger

# Agents
from agents.planner import PlannerAgent
from agents.executor import ExecutorAgent
from agents.reviewer import ReviewerAgent

# Tools - These may not exist anymore
# from tools.builtin.python import Tool as PythonTool
# from tools.builtin.files import Tool as FilesTool

# Router - REMOVED
# from router.analyzer import TaskAnalyzer
# from router.executor import RoutingExecutor


async def demonstrate_integration():
    """展示完整的整合流程"""
    print("=" * 60)
    print("🚀 Core Agentic Brain - Full Integration Demo")
    print("=" * 60)

    # 1. 初始化提示詞系統
    print("\n📚 Step 1: Loading Prompts System")
    prompt_loader = get_prompt_loader()

    # 展示提示詞載入
    planner_prompt = prompt_loader.get("planner.system")
    print(f"✅ Planner prompt loaded: {planner_prompt[:50]}...")

    python_tool_prompt = prompt_loader.get_tool_prompt("python", "system")
    print(f"✅ Python tool prompt loaded: {python_tool_prompt[:50]}...")

    # 2. 初始化工具
    print("\n🔧 Step 2: Initializing Tools")
    python_tool = PythonTool()
    files_tool = FilesTool()

    # 展示工具提示詞整合
    print(f"✅ Python tool system prompt: {python_tool.get_system_prompt()[:50]}...")
    print(f"✅ Files tool system prompt: {files_tool.get_system_prompt()[:50]}...")

    # 3. 初始化 Agents
    print("\n🤖 Step 3: Initializing Agents")
    planner = PlannerAgent()
    executor = ExecutorAgent()
    reviewer = ReviewerAgent()

    print(f"✅ Planner initialized with prompt from YAML")
    print(f"✅ Executor initialized with prompt from YAML")
    print(f"✅ Reviewer initialized with prompt from YAML")

    # 4. 展示工作流程
    print("\n🔄 Step 4: Demonstrating Workflow")

    # 測試任務
    test_task = "Create a Python function to calculate fibonacci numbers and save it to a file"
    context = TaskContext(prompt=test_task)

    print(f"\n📋 Task: {test_task}")

    # 4.1 規劃階段
    print("\n▶️  Planning Phase...")
    plan_result = await planner.execute(context)
    if plan_result.success:
        print(f"✅ Plan created: {plan_result.response[:100]}...")

    # 4.2 執行階段
    print("\n▶️  Execution Phase...")
    # 更新 context 包含計畫
    context.metadata["plan"] = {"steps": [
        {"number": 1, "description": "Create fibonacci function"},
        {"number": 2, "description": "Save to file"}
    ]}

    exec_result = await executor.execute(context)
    if exec_result.success:
        print(f"✅ Execution complete: {exec_result.response[:100]}...")

    # 4.3 審查階段
    print("\n▶️  Review Phase...")
    context.metadata["previous_result"] = exec_result.response
    review_result = await reviewer.execute(context)
    if review_result.success:
        print(f"✅ Review complete: {review_result.response[:100]}...")

    # 5. 展示工具執行
    print("\n🛠️  Step 5: Direct Tool Execution Demo")

    # 執行 Python 代碼
    python_code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# 測試
for i in range(10):
    print(f"fib({i}) = {fibonacci(i)}")
"""

    print(f"\n📝 Executing Python code...")
    result = await python_tool.execute(code=python_code)
    if result["success"]:
        print(f"✅ Python execution successful:")
        print(f"   Output: {result['output'][:200]}")

    # 檔案操作
    print(f"\n💾 Saving to file...")
    file_result = await files_tool.execute(
        operation="write",
        path="workspace/fibonacci.py",
        content=python_code
    )
    if file_result["success"]:
        print(f"✅ File saved to: {file_result['path']}")

    # 6. 展示路由系統
    print("\n🎯 Step 6: Routing System Demo")

    analyzer = TaskAnalyzer()
    agents_dict = {
        "planner": planner,
        "executor": executor,
        "reviewer": reviewer
    }
    routing_executor = RoutingExecutor(agents_dict)

    # 分析任務
    decision = await analyzer.analyze(context)
    print(f"✅ Task analyzed: {decision.strategy} strategy, complexity: {decision.complexity.value}")

    # 執行路由
    final_result = await routing_executor.execute(decision, context)
    if final_result.success:
        print(f"✅ Routed execution complete")

    print("\n" + "=" * 60)
    print("🎉 Integration Demo Complete!")
    print("=" * 60)

    # 總結連動關係
    print("\n📊 Integration Summary:")
    print("├── Agents ✅")
    print("│   ├── Load prompts from YAML ✅")
    print("│   ├── Use PromptLoader ✅")
    print("│   └── Call Tools ✅")
    print("├── Prompts ✅")
    print("│   ├── Centralized management ✅")
    print("│   ├── Parameter substitution ✅")
    print("│   └── Multi-language support ready")
    print("└── Tools ✅")
    print("    ├── Load prompts from YAML ✅")
    print("    ├── Use PromptLoader ✅")
    print("    └── Safe execution ✅")


async def test_prompt_formatting():
    """測試提示詞格式化功能"""
    print("\n🔤 Testing Prompt Formatting...")

    loader = get_prompt_loader()

    # 測試參數替換
    formatted = loader.get(
        "planner.planning_prompt",
        user_query="Build a web scraper",
        history="Previous conversation about Python"
    )

    print(f"✅ Formatted prompt with parameters:")
    print(f"   {formatted[:150]}...")

    # 測試工具提示詞
    exec_prompt = loader.get(
        "tools.python_tool.execution",
        code="print('Hello, World!')"
    )
    print(f"\n✅ Tool execution prompt:")
    print(f"   {exec_prompt[:150]}...")


async def main():
    """主函數"""
    try:
        # 運行整合示範
        await demonstrate_integration()

        # 測試格式化
        await test_prompt_formatting()

        print("\n✨ All systems integrated and operational!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    # 確保工作目錄存在
    Path("workspace").mkdir(exist_ok=True)

    # 運行示範
    exit_code = asyncio.run(main())
    exit(exit_code)
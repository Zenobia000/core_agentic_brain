#!/usr/bin/env python3
"""Test the integration between agents, prompts, and tools."""

import asyncio
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from core.prompt_loader import get_prompt_loader
from agents.planner import PlannerAgent
from agents.executor import ExecutorAgent
from agents.reviewer import ReviewerAgent
from core.types import TaskContext


def test_prompt_loader():
    """Test that prompt loader works correctly."""
    print("Testing Prompt Loader...")

    loader = get_prompt_loader()

    # Test loading agent prompts
    planner_prompt = loader.get("planner.system")
    executor_prompt = loader.get("executor.system")
    reviewer_prompt = loader.get("reviewer.system")

    assert not planner_prompt.startswith("# Prompt not found"), "Planner prompt not found"
    assert not executor_prompt.startswith("# Prompt not found"), "Executor prompt not found"
    assert not reviewer_prompt.startswith("# Prompt not found"), "Reviewer prompt not found"

    print("✅ All prompts loaded successfully")
    print(f"  - Planner prompt: {len(planner_prompt)} chars")
    print(f"  - Executor prompt: {len(executor_prompt)} chars")
    print(f"  - Reviewer prompt: {len(reviewer_prompt)} chars")

    # Test tool prompts
    python_prompt = loader.get_tool_prompt("python", "system")
    file_prompt = loader.get_tool_prompt("file", "system")

    print(f"  - Python tool prompt: {len(python_prompt)} chars")
    print(f"  - File tool prompt: {len(file_prompt)} chars")

    return True


async def test_agents_with_prompts():
    """Test that agents use prompts correctly."""
    print("\nTesting Agents with Prompts...")

    # Initialize agents
    planner = PlannerAgent()
    executor = ExecutorAgent()
    reviewer = ReviewerAgent()

    # Check that system prompts are loaded from YAML
    planner_prompt = planner.get_system_prompt()
    executor_prompt = executor.get_system_prompt()
    reviewer_prompt = reviewer.get_system_prompt()

    # Verify prompts are not empty and contain expected content
    assert len(planner_prompt) > 100, "Planner prompt too short"
    assert "planning specialist" in planner_prompt.lower(), "Planner prompt missing key content"

    assert len(executor_prompt) > 100, "Executor prompt too short"
    assert "execution specialist" in executor_prompt.lower(), "Executor prompt missing key content"

    assert len(reviewer_prompt) > 100, "Reviewer prompt too short"
    assert "review specialist" in reviewer_prompt.lower(), "Reviewer prompt missing key content"

    print("✅ All agents loaded prompts correctly")
    print(f"  - Planner: {planner_prompt[:50]}...")
    print(f"  - Executor: {executor_prompt[:50]}...")
    print(f"  - Reviewer: {reviewer_prompt[:50]}...")

    return True


def test_prompt_formatting():
    """Test prompt formatting with parameters."""
    print("\nTesting Prompt Formatting...")

    loader = get_prompt_loader()

    # Test planning prompt with parameters
    planning_prompt = loader.get(
        "planner.planning_prompt",
        user_query="Create a Python function",
        history="[]"
    )

    assert "Create a Python function" in planning_prompt, "Parameter substitution failed"
    assert "[]" in planning_prompt, "History parameter not substituted"

    print("✅ Prompt formatting works correctly")
    print(f"  - Formatted prompt: {planning_prompt[:100]}...")

    return True


async def main():
    """Run all integration tests."""
    print("=" * 60)
    print("TESTING AGENTS-PROMPTS-TOOLS INTEGRATION")
    print("=" * 60)

    try:
        # Test prompt loader
        test_prompt_loader()

        # Test agents with prompts
        await test_agents_with_prompts()

        # Test prompt formatting
        test_prompt_formatting()

        print("\n" + "=" * 60)
        print("🎉 ALL INTEGRATION TESTS PASSED!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
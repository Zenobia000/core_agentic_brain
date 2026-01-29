#!/usr/bin/env python3
"""Test Layer 1 functionality."""

import asyncio
from router.analyzer import TaskAnalyzer
from router.executor import RoutingExecutor
from core.types import TaskContext, AgentRole
from agents.planner import PlannerAgent
from agents.executor import ExecutorAgent
from agents.reviewer import ReviewerAgent
from core.logger import logger


async def test_layer1():
    """Test Layer 1 routing and execution."""
    logger.info("Starting Layer 1 test")

    # Initialize components
    analyzer = TaskAnalyzer()

    # Create agents
    agents = {
        AgentRole.PLANNER.value: PlannerAgent(),
        AgentRole.EXECUTOR.value: ExecutorAgent(),
        AgentRole.REVIEWER.value: ReviewerAgent()
    }
    executor = RoutingExecutor(agents)

    # Test different types of tasks
    test_cases = [
        "What is the weather today?",
        "Create a Python function to calculate fibonacci",
        "Design a microservice architecture for e-commerce"
    ]

    for prompt in test_cases:
        logger.info(f"Testing prompt: {prompt}")

        # Create context
        context = TaskContext(prompt=prompt)

        # Analyze task
        decision = await analyzer.analyze(context)
        logger.info(f"Decision - Strategy: {decision.strategy}, Complexity: {decision.complexity.value}")
        logger.info(f"Agents: {[a.value for a in decision.agents]}")
        logger.info(f"Reasoning: {decision.reasoning}")

        # Execute task (if not requiring actual LLM)
        # Note: This will fail without proper LLM setup, but will test the flow
        try:
            result = await executor.execute(decision, context)
            if result.success:
                logger.info("Execution successful")
            else:
                logger.warning(f"Execution failed: {result.error}")
        except Exception as e:
            logger.error(f"Execution error: {e}")

        print("-" * 50)


if __name__ == "__main__":
    asyncio.run(test_layer1())
#!/usr/bin/env python3
"""Test Layer 1 routing without LLM dependency."""

import asyncio
from router.analyzer import TaskAnalyzer
from core.types import TaskContext
from core.logger import logger


async def test_routing():
    """Test routing analysis without LLM."""
    logger.info("Testing routing analyzer")

    # Initialize analyzer
    analyzer = TaskAnalyzer()

    # Test cases with expected complexity
    test_cases = [
        ("What is 2+2?", "SIMPLE"),
        ("List all files in the directory", "SIMPLE"),
        ("Create a function to sort an array", "MODERATE"),
        ("Analyze the performance of this algorithm", "MODERATE"),
        ("Design a distributed caching system", "COMPLEX"),
        ("Integrate multiple APIs and optimize for latency", "COMPLEX"),
    ]

    for prompt, expected_complexity in test_cases:
        # Create context
        context = TaskContext(prompt=prompt)

        # Analyze task
        decision = analyzer.analyze(context)

        # Log results
        print(f"\nPrompt: {prompt}")
        print(f"  Expected: {expected_complexity}")
        print(f"  Detected: {decision.complexity.value.upper()}")
        print(f"  Strategy: {decision.strategy}")
        print(f"  Agents: {[a.value for a in decision.agents]}")

        # Check if complexity matches expectation
        if decision.complexity.value.upper() == expected_complexity:
            print("  ✓ Correct complexity detection")
        else:
            print("  ✗ Incorrect complexity detection")

        logger.info(
            "Routing analysis complete",
            prompt=prompt[:30],
            complexity=decision.complexity.value,
            strategy=decision.strategy
        )

    print("\n" + "="*50)
    print("Routing test completed!")


if __name__ == "__main__":
    asyncio.run(test_routing())
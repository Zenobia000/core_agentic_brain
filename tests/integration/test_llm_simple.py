#!/usr/bin/env python3
"""Simple test without tools"""

import asyncio
from dotenv import load_dotenv
from core.llm import LLMWrapper
# LLMResponse is in core.llm module

# Load environment variables
load_dotenv()

async def test_simple():
    """Test LLM directly without tools"""
    print("Testing Core Agentic Brain - Simple Mode\n")

    # Simple config without tools
    llm_config = {
        "provider": "openai",
        "model": "gpt-3.5-turbo",
        "temperature": 0.7,
        "max_tokens": 100
    }

    # Initialize LLM
    llm = LLMWrapper(llm_config)
    print("✅ LLM initialized")

    # Test queries
    queries = [
        "What is 2+2?",
        "Tell me a joke in one sentence.",
        "What is the capital of France?"
    ]

    for query in queries:
        print(f"\nUser: {query}")
        messages = [{"role": "user", "content": query}]

        try:
            response = await llm.generate(messages)
            print(f"AI: {response.content}")
        except Exception as e:
            print(f"Error: {e}")

    print("\n✅ All tests completed!")

if __name__ == "__main__":
    asyncio.run(test_simple())
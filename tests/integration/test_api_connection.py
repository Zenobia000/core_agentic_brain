#!/usr/bin/env python3
"""Test script to verify OpenAI API connection"""

import asyncio
import os
from dotenv import load_dotenv
from core.llm import LLMWrapper

# Load environment variables
load_dotenv()

async def test_llm():
    """Test LLM connection and basic functionality"""
    print("Testing OpenAI API connection...")

    # Check if API key is loaded
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment")
        return

    print(f"✅ API key loaded (starts with: {api_key[:10]}...)")

    # Initialize LLM
    try:
        llm_config = {
            "provider": "openai",
            "model": "gpt-3.5-turbo",
            "temperature": 0.7,
            "max_tokens": 100
        }
        llm = LLMWrapper(llm_config)
        print("✅ LLM wrapper initialized")
    except Exception as e:
        print(f"❌ Failed to initialize LLM: {e}")
        return

    # Test simple query
    try:
        messages = [
            {"role": "user", "content": "What is 2+2? Answer in one word."}
        ]
        response = await llm.generate(messages)
        print(f"✅ LLM response: {response.content}")
    except Exception as e:
        print(f"❌ Failed to generate response: {e}")
        return

    print("\n🎉 All tests passed!")

if __name__ == "__main__":
    asyncio.run(test_llm())
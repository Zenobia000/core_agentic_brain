#!/usr/bin/env python3
"""Test main application with minimal mode"""

import asyncio
from pathlib import Path
from dotenv import load_dotenv
from core.agent import Agent
from core.config import load_config

# Load environment variables
load_dotenv()

async def test_minimal_mode():
    """Test the application in minimal mode (Layer 0 only)"""
    print("Testing Core Agentic Brain - Minimal Mode\n")

    # Load config
    config_path = Path("config.yaml")
    config = load_config(config_path) if config_path.exists() else {}

    # Initialize agent
    try:
        agent = Agent(config)
        print("✅ Agent initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        return

    # Test simple query
    try:
        query = "What is 2+2?"
        print(f"\nUser: {query}")
        response = await agent.process(query)
        print(f"AI: {response}")
        print("\n✅ Query processed successfully!")
    except Exception as e:
        print(f"❌ Failed to process query: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_minimal_mode())
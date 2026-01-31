#!/usr/bin/env python3
"""Test main application with Kernel-based architecture"""

import asyncio
from pathlib import Path
from dotenv import load_dotenv
from core.kernel import Kernel
from core.config import load_config

# Load environment variables
load_dotenv()


async def test_kernel_execution():
    """Test the Kernel-based OKR architecture"""
    print("Testing Core Agentic Brain - Kernel Architecture\n")

    # Load config
    config_path = Path("config.yaml")
    config = load_config(config_path) if config_path.exists() else {}

    # Initialize kernel
    try:
        kernel = Kernel()
        print("Kernel initialized successfully")
    except Exception as e:
        print(f"Failed to initialize kernel: {e}")
        return

    # Test simple query
    try:
        query = "What is 2+2?"
        print(f"\nUser: {query}")
        result = await kernel.execute(query)
        if result.success:
            print(f"AI: {result.response}")
            print("\nQuery processed successfully!")
        else:
            print(f"Execution failed: {result.error}")
    except Exception as e:
        print(f"Failed to process query: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_kernel_execution())

"""
Pytest configuration and fixtures.
"""

import pytest
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_config():
    """Test configuration"""
    return {
        "llm": {
            "provider": "openai",
            "model": "gpt-3.5-turbo",
            "api_key": "test-key",
            "max_tokens": 100
        },
        "tools": {
            "enabled": ["python", "files"]
        },
        "agent": {
            "max_history": 10,
            "system_prompt": "Test agent"
        }
    }


@pytest.fixture
def sample_messages():
    """Sample conversation messages"""
    from core.types import Message, MessageRole
    return [
        Message(role=MessageRole.SYSTEM, content="You are a test assistant"),
        Message(role=MessageRole.USER, content="Hello"),
        Message(role=MessageRole.ASSISTANT, content="Hi there!")
    ]
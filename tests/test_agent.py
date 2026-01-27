# tests/test_agent.py
import pytest
from unittest.mock import patch, MagicMock
from core.agent import Agent

# A fixture to create a mock configuration
@pytest.fixture
def mock_config():
    return {
        "llm": {
            "provider": "openai",
            "model": "gpt-test",
            "api_key": "fake_api_key"
        },
        "agent": {
            "name": "TestAgent",
            "max_iterations": 3,
            "max_thought_history": 5
        }
    }

# Patch the get_config function to return our mock config
@patch('core.config.get_config')
def test_agent_initialization(mock_get_config, mock_config):
    """
    Tests if the Agent initializes correctly.
    """
    # Arrange: Make get_config return our mock data
    mock_get_config.return_value = mock_config
    
    # We also need to mock the LLMClient to avoid a real API call
    with patch('core.agent.LLMClient') as MockLLMClient:
        # Arrange
        mock_llm_instance = MockLLMClient.return_value
        mock_llm_instance.generate.return_value = '{"thought": "init", "action": "init"}'

        # Act
        agent = Agent()

        # Assert
        assert agent.name == "TestAgent"
        assert agent.max_iterations == 3
        assert isinstance(agent.llm_client, MagicMock)
        assert "You are TestAgent" in agent.system_prompt
        # Check that tools were discovered
        assert "Available tools:" in agent.tool_descriptions


@pytest.mark.skip(reason="This is a more complex integration test that requires mocking the LLM loop.")
@patch('core.config.get_config')
def test_agent_run_loop(mock_get_config, mock_config):
    """
    A placeholder for a more complete test of the agent's run loop.
    """
    # Arrange
    mock_get_config.return_value = mock_config

    with patch('core.agent.LLMClient') as MockLLMClient:
        # Act & Assert
        # ... more complex mocking logic would go here ...
        pass


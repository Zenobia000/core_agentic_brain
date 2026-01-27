# tests/test_tool_manager.py
import pytest
from core.tool_manager import register_tool, get_tools, execute_tool, get_tool_descriptions

# Clear the registry before each test module run to ensure isolation
def setup_module(module):
    get_tools().clear()

@register_tool
def mock_tool_one(param1: str, param2: int = 10) -> str:
    """A mock tool for testing."""
    return f"{param1}-{param2}"

@register_tool
def mock_tool_two() -> str:
    """Another mock tool."""
    return "success"

def test_register_tool():
    """Tests if tools are correctly registered."""
    tools = get_tools()
    assert "mock_tool_one" in tools
    assert "mock_tool_two" in tools
    assert callable(tools["mock_tool_one"])

def test_get_tool_descriptions():
    """Tests if descriptions are generated correctly."""
    descriptions = get_tool_descriptions()
    assert "mock_tool_one(param1: str, param2: int = 10): A mock tool for testing." in descriptions
    assert "mock_tool_two(): Another mock tool." in descriptions

def test_execute_tool_success():
    """Tests successful execution of a tool."""
    result = execute_tool("mock_tool_one", param1="test")
    assert result == "test-10"

    result_with_arg = execute_tool("mock_tool_one", param1="hello", param2=99)
    assert result_with_arg == "hello-99"

    result_two = execute_tool("mock_tool_two")
    assert result_two == "success"

def test_execute_tool_not_found():
    """Tests execution of a non-existent tool."""
    result = execute_tool("non_existent_tool")
    assert "Error: Tool 'non_existent_tool' not found" in result

def test_execute_tool_missing_argument():
    """Tests execution with missing required arguments."""
    with pytest.raises(TypeError):
        # This should fail because param1 is required
        execute_tool("mock_tool_one")

def test_prevent_duplicate_registration():
    """Tests that registering a tool with a duplicate name raises an error."""
    with pytest.raises(ValueError, match="Tool 'mock_tool_two' is already registered."):
        @register_tool
        def mock_tool_two(): # Duplicate name
            return "failure"


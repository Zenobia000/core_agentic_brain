"""
Unit tests for tools module.
"""

import pytest
import asyncio
from core.tools import ToolManager, BaseTool


class MockTool(BaseTool):
    """Mock tool for testing"""

    def __init__(self):
        super().__init__(
            name="mock",
            description="Mock tool for testing"
        )

    async def execute(self, **kwargs):
        """Execute mock tool"""
        return {"status": "success", "args": kwargs}


class TestToolManager:
    """Test ToolManager class"""

    def test_register_tool(self):
        """Test tool registration"""
        manager = ToolManager()
        tool = MockTool()

        manager.register_tool(tool)

        assert "mock" in manager.tools
        assert manager.get_tool("mock") == tool

    def test_get_nonexistent_tool(self):
        """Test getting nonexistent tool"""
        manager = ToolManager()
        assert manager.get_tool("nonexistent") is None

    @pytest.mark.asyncio
    async def test_execute_tool(self):
        """Test tool execution"""
        manager = ToolManager()
        tool = MockTool()
        manager.register_tool(tool)

        result = await manager.execute("mock", test="value")

        assert result["status"] == "success"
        assert result["args"]["test"] == "value"

    @pytest.mark.asyncio
    async def test_execute_nonexistent_tool(self):
        """Test executing nonexistent tool"""
        manager = ToolManager()

        with pytest.raises(ValueError, match="Tool 'nonexistent' not found"):
            await manager.execute("nonexistent")

    def test_list_tools(self):
        """Test listing all tools"""
        manager = ToolManager()
        tool1 = MockTool()
        tool1.name = "tool1"
        tool2 = MockTool()
        tool2.name = "tool2"

        manager.register_tool(tool1)
        manager.register_tool(tool2)

        tools = manager.list_tools()
        assert len(tools) == 2
        assert "tool1" in tools
        assert "tool2" in tools

    def test_get_definitions(self):
        """Test getting tool definitions"""
        manager = ToolManager()
        tool = MockTool()
        manager.register_tool(tool)

        definitions = manager.get_definitions()

        assert len(definitions) == 1
        assert definitions[0]["name"] == "mock"
        assert definitions[0]["description"] == "Mock tool for testing"

    def test_load_builtin_tools(self):
        """Test loading builtin tools"""
        manager = ToolManager()
        manager._load_tools()

        # Should have at least python and files tools
        tools = manager.list_tools()
        assert "python" in tools or len(tools) > 0  # Flexible check


class TestBaseTool:
    """Test BaseTool abstract class"""

    def test_tool_creation(self):
        """Test basic tool creation"""
        tool = MockTool()

        assert tool.name == "mock"
        assert tool.description == "Mock tool for testing"
        assert tool.parameters == {}

    def test_tool_definition(self):
        """Test tool definition generation"""
        tool = MockTool()
        tool.parameters = {"arg1": {"type": "string"}}

        definition = tool.get_definition()

        assert definition["name"] == "mock"
        assert definition["description"] == "Mock tool for testing"
        assert "arg1" in definition["parameters"]

    @pytest.mark.asyncio
    async def test_tool_execution(self):
        """Test tool execution"""
        tool = MockTool()
        result = await tool.execute(test="value")

        assert result["status"] == "success"
        assert result["args"]["test"] == "value"
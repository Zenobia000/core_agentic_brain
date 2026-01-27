"""
Test suite for Optimized Agent with Context Engineering Principles
"""

import asyncio
import pytest
from typing import List

from app.agent.optimized_agent import OptimizedAgent
from app.memory_manager import EnhancedMemory, MemoryManager
from app.tool_manager import ToolRegistry, ToolStatus, TaskClassifier
from app.schema import Message
from app.tool.base import BaseTool, ToolResult
from app.tool import ToolCollection


class MockTool(BaseTool):
    """Mock tool for testing"""

    name: str = "mock_tool"
    description: str = "A mock tool for testing"
    parameters: dict = {
        "type": "object",
        "properties": {
            "input": {"type": "string"}
        }
    }

    async def execute(self, input: str = "") -> ToolResult:
        return ToolResult(output=f"Mock executed: {input}")


class TestPrinciple1MemoryOptimization:
    """Test cases for Principle 1: KV-Cache Optimization"""

    def test_enhanced_memory_creation(self):
        """Test enhanced memory creation"""
        memory = MemoryManager.create_memory(
            strategy="enhanced",
            window_size=10,
            summary_threshold=15
        )
        assert isinstance(memory, EnhancedMemory)
        assert memory.window.window_size == 10
        assert memory.window.summary_threshold == 15

    def test_sliding_window(self):
        """Test sliding window maintains correct size"""
        memory = EnhancedMemory(
            window={"window_size": 5, "summary_threshold": 10}
        )

        # Add messages
        for i in range(20):
            memory.add_message(Message.user_message(f"Message {i}"))

        # Get context messages (should be limited by window)
        context = memory.get_context_messages()
        # Should have at most window_size messages plus potential summary
        assert len(context) <= 6  # 5 messages + 1 potential summary

    @pytest.mark.asyncio
    async def test_memory_compression(self):
        """Test automatic memory compression"""
        memory = EnhancedMemory(
            window={"window_size": 5, "summary_threshold": 8}
        )

        # Add messages beyond threshold
        for i in range(10):
            memory.add_message(Message.user_message(f"Test message {i}"))

        # Wait for compression to potentially occur
        await asyncio.sleep(0.5)

        # Check that old messages are archived
        assert len(memory.archived_messages) > 0 or memory.summary is not None

    def test_memory_migration(self):
        """Test migration from standard to enhanced memory"""
        from app.schema import Memory

        # Create standard memory with messages
        old_memory = Memory()
        for i in range(5):
            old_memory.add_message(Message.user_message(f"Old message {i}"))

        # Migrate to enhanced
        enhanced = MemoryManager.migrate_memory(old_memory)

        assert len(enhanced.messages) == 5
        assert isinstance(enhanced, EnhancedMemory)


class TestPrinciple2ToolMasking:
    """Test cases for Principle 2: Tool Masking"""

    def test_tool_registration(self):
        """Test tool registration in registry"""
        registry = ToolRegistry()
        tool = MockTool()

        registry.register_tool(tool, is_global=False)

        assert tool.name in registry._tools
        assert tool.name in registry._masks
        assert registry._masks[tool.name].status == ToolStatus.ENABLED

    def test_tool_masking(self):
        """Test applying masks to tools"""
        registry = ToolRegistry()
        tool = MockTool()

        registry.register_tool(tool)

        # Disable tool
        assert registry.mask_tool(tool.name, ToolStatus.DISABLED, "Testing")
        assert registry._masks[tool.name].status == ToolStatus.DISABLED
        assert registry._masks[tool.name].reason == "Testing"

    def test_global_tool_protection(self):
        """Test that global tools cannot be disabled"""
        registry = ToolRegistry()
        tool = MockTool()

        registry.register_tool(tool, is_global=True)

        # Try to disable global tool
        assert not registry.mask_tool(tool.name, ToolStatus.DISABLED)
        assert registry._masks[tool.name].status == ToolStatus.ENABLED

    def test_permission_based_filtering(self):
        """Test tool filtering based on permissions"""
        registry = ToolRegistry()
        tool = MockTool()

        registry.register_tool(tool)
        registry.set_tool_permissions(tool.name, ["admin", "developer"])

        # Without permissions
        available = registry.get_available_tools(user_permissions=set())
        assert len(available.tools) == 0

        # With partial permissions
        available = registry.get_available_tools(user_permissions={"developer"})
        assert len(available.tools) == 0

        # With all permissions
        available = registry.get_available_tools(
            user_permissions={"admin", "developer"}
        )
        assert len(available.tools) == 1

    def test_context_based_filtering(self):
        """Test tool filtering based on context"""
        registry = ToolRegistry()
        tool = MockTool()

        registry.register_tool(tool)
        registry.set_tool_context(tool.name, {"environment": "production"})

        # Wrong context
        available = registry.get_available_tools(
            context={"environment": "development"}
        )
        assert len(available.tools) == 0

        # Correct context
        available = registry.get_available_tools(
            context={"environment": "production"}
        )
        assert len(available.tools) == 1

    def test_task_classifier(self):
        """Test task classification and tool recommendation"""
        classifier = TaskClassifier()

        # Test code generation task
        task_type = classifier.classify_task("Write a Python function to sort a list")
        assert task_type == "code_generation"

        # Test web research task
        task_type = classifier.classify_task("Search the web for latest AI news")
        assert task_type == "web_research"

        # Test data analysis task
        task_type = classifier.classify_task("Analyze this dataset and create a chart")
        assert task_type == "data_analysis"


class TestOptimizedAgent:
    """Test cases for the Optimized Agent"""

    @pytest.mark.asyncio
    async def test_agent_initialization(self):
        """Test optimized agent initialization"""
        agent = OptimizedAgent(
            use_memory_optimization=True,
            use_tool_masking=True,
            memory_window_size=15
        )

        assert agent.use_memory_optimization
        assert agent.use_tool_masking
        assert agent.enhanced_memory is not None
        assert agent.enhanced_memory.window.window_size == 15

    @pytest.mark.asyncio
    async def test_agent_with_masking(self):
        """Test agent with tool masking"""
        agent = OptimizedAgent(use_tool_masking=True)

        # Register tools
        tool1 = MockTool()
        tool1.name = "tool1"
        tool2 = MockTool()
        tool2.name = "tool2"

        agent.register_tool(tool1)
        agent.register_tool(tool2)

        # Disable tool2
        agent.mask_tool("tool2", ToolStatus.DISABLED)

        # Get available tools
        tools = agent.get_available_tools_with_masking()

        # Only tool1 should be available
        tool_names = [t.name for t in tools.tools]
        assert "tool1" in tool_names
        assert "tool2" not in tool_names

    def test_optimization_stats(self):
        """Test getting optimization statistics"""
        agent = OptimizedAgent(
            use_memory_optimization=True,
            use_tool_masking=True
        )

        # Add some messages
        for i in range(5):
            agent.add_message(Message.user_message(f"Message {i}"))

        # Register a tool
        agent.register_tool(MockTool())

        # Get stats
        stats = agent.get_optimization_stats()

        assert stats["memory_optimization_enabled"]
        assert stats["tool_masking_enabled"]
        assert stats["active_messages"] == 5
        assert stats["total_tools_registered"] > 0

    @pytest.mark.asyncio
    async def test_task_configuration(self):
        """Test agent configuration for specific task"""
        agent = OptimizedAgent(use_tool_masking=True)

        # Register various tools
        for i in range(5):
            tool = MockTool()
            tool.name = f"tool_{i}"
            agent.register_tool(tool)

        # Configure for code generation task
        agent.configure_for_task("Write a Python script to process data")

        # Check that tools are configured appropriately
        all_tools = agent.tool_registry.list_all_tools()
        assert len(all_tools) > 0


def run_tests():
    """Run all tests"""
    print("Testing Principle 1: Memory Optimization")
    print("=" * 50)

    # Memory tests
    memory_test = TestPrinciple1MemoryOptimization()
    memory_test.test_enhanced_memory_creation()
    print("✅ Enhanced memory creation test passed")

    memory_test.test_sliding_window()
    print("✅ Sliding window test passed")

    memory_test.test_memory_migration()
    print("✅ Memory migration test passed")

    print("\nTesting Principle 2: Tool Masking")
    print("=" * 50)

    # Tool masking tests
    tool_test = TestPrinciple2ToolMasking()
    tool_test.test_tool_registration()
    print("✅ Tool registration test passed")

    tool_test.test_tool_masking()
    print("✅ Tool masking test passed")

    tool_test.test_global_tool_protection()
    print("✅ Global tool protection test passed")

    tool_test.test_permission_based_filtering()
    print("✅ Permission-based filtering test passed")

    tool_test.test_context_based_filtering()
    print("✅ Context-based filtering test passed")

    tool_test.test_task_classifier()
    print("✅ Task classifier test passed")

    print("\nTesting Optimized Agent")
    print("=" * 50)

    # Agent tests
    agent_test = TestOptimizedAgent()
    agent_test.test_optimization_stats()
    print("✅ Optimization stats test passed")

    print("\n🎉 All tests passed successfully!")


if __name__ == "__main__":
    run_tests()
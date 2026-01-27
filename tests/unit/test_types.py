"""
Unit tests for core data types.
"""

import pytest
from datetime import datetime
from core.types import (
    Message, MessageRole, TaskComplexity, ToolCall,
    ToolDefinition, AgentContext, TaskResult, RouterDecision
)


class TestMessage:
    """Test Message dataclass"""

    def test_message_creation(self):
        """Test basic message creation"""
        msg = Message(
            role=MessageRole.USER,
            content="Test message"
        )
        assert msg.role == MessageRole.USER
        assert msg.content == "Test message"
        assert isinstance(msg.timestamp, datetime)
        assert msg.metadata == {}
        assert msg.tool_call_id is None

    def test_message_with_metadata(self):
        """Test message with metadata"""
        metadata = {"key": "value"}
        msg = Message(
            role=MessageRole.ASSISTANT,
            content="Response",
            metadata=metadata
        )
        assert msg.metadata == metadata


class TestToolCall:
    """Test ToolCall dataclass"""

    def test_tool_call_creation(self):
        """Test tool call creation"""
        call = ToolCall(
            id="test-123",
            name="python",
            arguments={"code": "print('hello')"}
        )
        assert call.id == "test-123"
        assert call.name == "python"
        assert call.status == "pending"
        assert call.result is None
        assert call.error is None

    def test_tool_call_status_update(self):
        """Test tool call status update"""
        call = ToolCall(
            id="test-456",
            name="files",
            arguments={"action": "list"}
        )
        call.status = "success"
        call.result = ["file1.txt", "file2.txt"]
        assert call.status == "success"
        assert call.result == ["file1.txt", "file2.txt"]


class TestTaskComplexity:
    """Test TaskComplexity enum"""

    def test_complexity_values(self):
        """Test complexity enum values"""
        assert TaskComplexity.SIMPLE.value == "simple"
        assert TaskComplexity.MODERATE.value == "moderate"
        assert TaskComplexity.COMPLEX.value == "complex"


class TestAgentContext:
    """Test AgentContext dataclass"""

    def test_context_creation(self, sample_messages):
        """Test context creation"""
        tools = {
            "python": ToolDefinition(
                name="python",
                description="Execute Python code",
                parameters={"code": {"type": "string"}}
            )
        }
        config = {"key": "value"}

        context = AgentContext(
            conversation=sample_messages,
            tools=tools,
            config=config
        )

        assert len(context.conversation) == 3
        assert "python" in context.tools
        assert context.config == config
        assert context.session_id is None


class TestTaskResult:
    """Test TaskResult dataclass"""

    def test_successful_result(self):
        """Test successful task result"""
        result = TaskResult(
            success=True,
            output="Task completed",
            complexity=TaskComplexity.SIMPLE,
            execution_time=1.5
        )
        assert result.success is True
        assert result.output == "Task completed"
        assert result.complexity == TaskComplexity.SIMPLE
        assert result.execution_time == 1.5
        assert result.errors == []

    def test_failed_result(self):
        """Test failed task result"""
        result = TaskResult(
            success=False,
            output=None,
            complexity=TaskComplexity.COMPLEX,
            execution_time=0.5,
            errors=["Error 1", "Error 2"]
        )
        assert result.success is False
        assert result.output is None
        assert len(result.errors) == 2


class TestRouterDecision:
    """Test RouterDecision dataclass"""

    def test_fast_path_decision(self):
        """Test fast path routing decision"""
        decision = RouterDecision(
            complexity=TaskComplexity.SIMPLE,
            strategy="fast_path",
            reasoning="Simple task, direct execution"
        )
        assert decision.complexity == TaskComplexity.SIMPLE
        assert decision.strategy == "fast_path"
        assert decision.agents == []

    def test_agent_path_decision(self):
        """Test agent path routing decision"""
        decision = RouterDecision(
            complexity=TaskComplexity.COMPLEX,
            strategy="agent_path",
            agents=["planner", "executor", "reviewer"],
            reasoning="Complex task requiring multiple agents"
        )
        assert decision.complexity == TaskComplexity.COMPLEX
        assert decision.strategy == "agent_path"
        assert len(decision.agents) == 3
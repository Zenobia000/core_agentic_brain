"""Core data types for the agent system."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from enum import Enum


class MessageRole(Enum):
    """Message role types."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class TaskComplexity(Enum):
    """Task complexity levels for routing."""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"


class AgentRole(Enum):
    """Agent role types."""
    PLANNER = "planner"
    EXECUTOR = "executor"
    REVIEWER = "reviewer"
    ORCHESTRATOR = "orchestrator"


@dataclass
class Message:
    """Represents a message in conversation."""
    role: MessageRole
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: Optional[float] = None


@dataclass
class ToolCall:
    """Represents a tool invocation."""
    name: str
    parameters: Dict[str, Any]
    result: Optional[Any] = None
    error: Optional[str] = None
    duration_ms: Optional[float] = None


@dataclass
class TaskContext:
    """Context for task execution."""
    prompt: str
    messages: List[Message] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    complexity: Optional[TaskComplexity] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionResult:
    """Result from task execution."""
    success: bool
    response: str
    tool_calls: List[ToolCall] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


@dataclass
class RoutingDecision:
    """Routing decision for a task."""
    strategy: str
    agents: List[AgentRole]
    complexity: TaskComplexity
    reasoning: str
    metadata: Dict[str, Any] = field(default_factory=dict)
"""
Core data types and structures for Core Agentic Brain.
Following minimalist philosophy: < 100 lines, essential types only.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union, Literal
from datetime import datetime
from enum import Enum


class MessageRole(Enum):
    """Message role enumeration"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class TaskComplexity(Enum):
    """Task complexity levels for routing decisions"""
    SIMPLE = "simple"      # Direct tool execution
    MODERATE = "moderate"  # Single agent handling
    COMPLEX = "complex"    # Multi-agent orchestration


@dataclass
class Message:
    """Conversation message"""
    role: MessageRole
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    tool_call_id: Optional[str] = None
    tool_calls: Optional[List[Dict]] = None


@dataclass
class ToolCall:
    """Tool invocation request"""
    id: str
    name: str
    arguments: Dict[str, Any]
    status: Literal["pending", "running", "success", "failed"] = "pending"
    result: Optional[Any] = None
    error: Optional[str] = None


@dataclass
class ToolDefinition:
    """Tool specification"""
    name: str
    description: str
    parameters: Dict[str, Any]
    category: str = "general"
    async_execution: bool = True


@dataclass
class AgentContext:
    """Agent execution context"""
    conversation: List[Message]
    tools: Dict[str, ToolDefinition]
    config: Dict[str, Any]
    session_id: Optional[str] = None
    user_id: Optional[str] = None


@dataclass
class TaskResult:
    """Task execution result"""
    success: bool
    output: Any
    complexity: TaskComplexity
    execution_time: float
    agent_path: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


@dataclass
class RouterDecision:
    """Routing decision for task execution"""
    complexity: TaskComplexity
    strategy: str  # "fast_path" or "agent_path"
    agents: List[str] = field(default_factory=list)
    reasoning: str = ""


# Type aliases for clarity
ConversationHistory = List[Message]
ToolRegistry = Dict[str, ToolDefinition]
ConfigDict = Dict[str, Any]
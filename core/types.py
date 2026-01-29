"""Core data types for the agent system."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from enum import Enum
import hashlib


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
    run_id: Optional[str] = None
    workspace_path: Optional[Path] = None


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


@dataclass
class ReactConfig:
    """ReAct loop configuration - eliminates hardcoded magic numbers.

    Follows Linus principle: Good defaults are better than options.
    All values have sensible defaults, can be overridden via config.yaml
    or TaskContext.metadata.
    """
    max_steps: int = 10                    # Maximum loop iterations
    token_budget: int = 8000               # Token budget limit
    token_warning_threshold: float = 0.8   # Warning threshold (80%)
    max_consecutive_errors: int = 3        # Circuit breaker threshold
    repetition_window: int = 5             # Window size for repetition detection
    enable_summarization: bool = True      # Auto-summarize on budget warning


@dataclass
class ToolCallSignature:
    """Tool call signature for repetition detection.

    Two calls with same name and args_hash are considered identical.
    """
    name: str
    args_hash: str

    @classmethod
    def from_tool_call(cls, name: str, arguments: str) -> "ToolCallSignature":
        """Create signature from tool call."""
        args_hash = hashlib.md5(arguments.encode()).hexdigest()[:8]
        return cls(name=name, args_hash=args_hash)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ToolCallSignature):
            return False
        return self.name == other.name and self.args_hash == other.args_hash

    def __hash__(self) -> int:
        return hash((self.name, self.args_hash))
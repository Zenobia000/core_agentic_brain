"""
Structured event system for thinking chain visualization
"""
from typing import Optional, Dict, Any, List, Literal, Callable
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum
import uuid
import asyncio


class EventPhase(str, Enum):
    """Event phases in agent execution"""
    THINK = "think"          # Agent is thinking/planning
    ACT = "act"              # Agent is taking action (tool call)
    OBSERVE = "observe"      # Agent is observing results
    FINAL = "final"          # Final answer for user
    ERROR = "error"          # Error occurred
    ARTIFACT = "artifact"    # Artifact generation


class EventRole(str, Enum):
    """Roles for event sources"""
    SYSTEM = "system"
    AGENT = "agent"
    TOOL = "tool"
    USER = "user"


class ArtifactType(str, Enum):
    """Types of artifacts"""
    FILE = "file"
    URL = "url"
    IMAGE = "image"
    TEXT = "text"
    CODE = "code"
    MARKDOWN = "markdown"


class Artifact(BaseModel):
    """Artifact metadata"""
    type: ArtifactType
    path: Optional[str] = None
    url: Optional[str] = None
    preview: Optional[str] = Field(None, description="First N lines/chars for preview")
    size: Optional[int] = None
    mime_type: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ToolInfo(BaseModel):
    """Tool execution information"""
    name: str
    input: Dict[str, Any] = Field(default_factory=dict)
    output: Optional[Any] = None
    duration_ms: Optional[int] = None
    status: Literal["running", "success", "failed", "timeout"] = "running"
    error: Optional[str] = None


class StepEvent(BaseModel):
    """Structured event for each step in agent execution"""
    # Core fields
    run_id: str = Field(description="Unique ID for this run/session")
    step_index: int = Field(description="Sequential step number")
    timestamp: datetime = Field(default_factory=datetime.now)

    # Event classification
    phase: EventPhase
    role: EventRole

    # Content
    message: Optional[str] = Field(None, description="Human-readable description")
    thinking: Optional[str] = Field(None, description="Agent's internal reasoning")

    # Tool execution
    tool: Optional[ToolInfo] = None

    # Artifacts
    artifacts: List[Artifact] = Field(default_factory=list)

    # Error handling
    error: Optional[str] = None
    error_type: Optional[str] = None

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        data = self.dict(exclude_none=True)
        # Convert datetime to ISO format
        data['timestamp'] = self.timestamp.isoformat()
        return data

    def to_ws_message(self) -> dict:
        """Format for WebSocket transmission"""
        return {
            "type": "step_event",
            "payload": self.to_dict()
        }


class ThinkingUpdate(BaseModel):
    """Thinking state update for UI"""
    summary: str
    detail: Optional[str] = None
    steps: List[str] = Field(default_factory=list)
    current_step: Optional[int] = None
    total_steps: Optional[int] = None

    def to_ws_message(self) -> dict:
        return {
            "type": "thinking_update",
            "payload": self.dict(exclude_none=True)
        }


class TaskUpdate(BaseModel):
    """Task progress update"""
    name: str
    current_phase: int
    total_phases: int
    phase_name: str
    waiting_for: Optional[str] = None
    progress_percentage: Optional[float] = None

    def to_ws_message(self) -> dict:
        return {
            "type": "task_update",
            "payload": self.dict(exclude_none=True)
        }


class TodoUpdate(BaseModel):
    """Todo list update"""
    items: List[Dict[str, Any]]

    def to_ws_message(self) -> dict:
        return {
            "type": "todo_update",
            "payload": {"items": self.items}
        }


class EventBus:
    """
    Event bus for managing and distributing structured events
    """
    def __init__(self):
        self.handlers: Dict[str, List[callable]] = {}
        self.event_history: List[StepEvent] = []
        self.current_run_id: Optional[str] = None
        self.step_counter: int = 0

    def register_handler(self, event_type: str, handler: callable):
        """Register an event handler"""
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        self.handlers[event_type].append(handler)

    def emit(self, event: StepEvent):
        """Emit an event to all registered handlers"""
        self.event_history.append(event)

        # Call handlers for this event type
        event_type = event.phase.value
        if event_type in self.handlers:
            for handler in self.handlers[event_type]:
                try:
                    # Check if handler is async
                    if asyncio.iscoroutinefunction(handler):
                        # Create task to run async handler
                        asyncio.create_task(handler(event))
                    else:
                        handler(event)
                except Exception as e:
                    print(f"Error in event handler: {e}")

        # Also call universal handlers
        if "*" in self.handlers:
            for handler in self.handlers["*"]:
                try:
                    # Check if handler is async
                    if asyncio.iscoroutinefunction(handler):
                        # Create task to run async handler
                        asyncio.create_task(handler(event))
                    else:
                        handler(event)
                except Exception as e:
                    print(f"Error in universal handler: {e}")

    def create_event(
        self,
        phase: EventPhase,
        role: EventRole = EventRole.AGENT,
        message: Optional[str] = None,
        **kwargs
    ) -> StepEvent:
        """Helper to create and emit an event"""
        if not self.current_run_id:
            self.current_run_id = str(uuid.uuid4())

        self.step_counter += 1

        event = StepEvent(
            run_id=self.current_run_id,
            step_index=self.step_counter,
            phase=phase,
            role=role,
            message=message,
            **kwargs
        )

        self.emit(event)
        return event

    def reset(self):
        """Reset for new run"""
        self.event_history.clear()
        self.current_run_id = None
        self.step_counter = 0

    def get_history(self) -> List[StepEvent]:
        """Get event history"""
        return self.event_history.copy()

    def get_final_answer(self) -> Optional[str]:
        """Extract final answer from events"""
        for event in reversed(self.event_history):
            if event.phase == EventPhase.FINAL:
                return event.message
        return None

    def get_artifacts(self) -> List[Artifact]:
        """Extract all artifacts from events"""
        artifacts = []
        for event in self.event_history:
            artifacts.extend(event.artifacts)
        return artifacts


# Global event bus instance
event_bus = EventBus()
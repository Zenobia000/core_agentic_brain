"""
Conversation Memory Management
Linus: One data structure to rule them all.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from core.types import Message


class CompactionStrategy(Enum):
    """Memory compaction strategies."""
    SIMPLE = "simple"      # Just keep recent N messages
    SUMMARY = "summary"    # Use LLM to summarize archived messages
    HYBRID = "hybrid"      # Summary for old, full for recent


@dataclass
class ConversationMemory:
    """Simple conversation memory with auto-compaction.

    Three-layer architecture:
    1. System context (permanent)
    2. Session history (sliding window)
    3. Working memory (ephemeral)

    Linus principle: Simple data structure, no special cases.
    """

    messages: List[Dict[str, Any]] = field(default_factory=list)

    # Configuration
    max_messages: int = 50              # Total max before compaction
    window_size: int = 20               # Recent messages to keep in full
    compaction_threshold: int = 40      # Trigger compaction at this count
    strategy: CompactionStrategy = CompactionStrategy.SIMPLE

    # State tracking
    total_messages_processed: int = 0
    compaction_count: int = 0

    def add(self, role: str, content: str, **kwargs) -> None:
        """Add message to memory, auto-compact if needed.

        Args:
            role: Message role (system, user, assistant, tool)
            content: Message content
            **kwargs: Additional fields (tool_call_id, name, etc.)
        """
        message = {"role": role, "content": content, **kwargs}
        self.messages.append(message)
        self.total_messages_processed += 1

        if len(self.messages) > self.compaction_threshold:
            self._compact()

    def add_tool_result(self, tool_call_id: str, content: str, name: str = None) -> None:
        """Add tool result message (OpenAI format)."""
        msg = {
            "role": "tool",
            "tool_call_id": tool_call_id,
            "content": content
        }
        if name:
            msg["name"] = name
        self.messages.append(msg)
        self.total_messages_processed += 1

    def add_assistant_with_tools(self, content: str, tool_calls: List[Dict]) -> None:
        """Add assistant message with tool calls."""
        self.messages.append({
            "role": "assistant",
            "content": content or "",
            "tool_calls": tool_calls
        })
        self.total_messages_processed += 1

    def get_messages(self) -> List[Dict[str, Any]]:
        """Get all messages for LLM call."""
        return self.messages.copy()

    def get_recent(self, n: int = None) -> List[Dict[str, Any]]:
        """Get recent N messages."""
        n = n or self.window_size
        return self.messages[-n:] if len(self.messages) > n else self.messages.copy()

    def _compact(self) -> None:
        """Compact message history to control memory usage.

        Strategy: Keep system messages + compaction marker + recent window.
        Linus: Simple is better than clever.
        """
        if self.strategy == CompactionStrategy.SIMPLE:
            self._compact_simple()
        elif self.strategy == CompactionStrategy.SUMMARY:
            self._compact_with_summary()
        else:
            self._compact_simple()  # Fallback

        self.compaction_count += 1

    def _compact_simple(self) -> None:
        """Simple compaction: keep system + marker + recent."""
        # Separate system messages (excluding compaction markers)
        system_msgs = [
            m for m in self.messages
            if m.get("role") == "system"
            and not m.get("content", "").startswith("[Context:")
        ]
        non_system = [m for m in self.messages if m.get("role") != "system"]

        # Keep only recent non-system messages
        recent = non_system[-self.window_size:] if len(non_system) > self.window_size else non_system
        archived_count = len(non_system) - len(recent)

        # Rebuild messages
        self.messages = []

        # Add system messages (usually just one)
        if system_msgs:
            self.messages.extend(system_msgs[:1])  # Keep first system msg

        # Add compaction marker if we archived anything
        if archived_count > 0:
            self.messages.append({
                "role": "system",
                "content": f"[Context: {archived_count} earlier messages compacted. Key context preserved above.]"
            })

        # Add recent messages
        self.messages.extend(recent)

    def _compact_with_summary(self) -> None:
        """Compaction with LLM summary (placeholder for async implementation)."""
        # For now, fall back to simple
        # TODO: Implement async LLM summarization
        self._compact_simple()

    def set_system_prompt(self, content: str) -> None:
        """Set or update system prompt (always first message)."""
        # Remove existing system prompts (but keep compaction markers)
        self.messages = [
            m for m in self.messages
            if m.get("role") != "system"
            or m.get("content", "").startswith("[Context:")
        ]

        # Insert system prompt at beginning
        self.messages.insert(0, {"role": "system", "content": content})

    def clear(self, keep_system: bool = True) -> None:
        """Clear memory, optionally keeping system prompt."""
        if keep_system:
            system = [
                m for m in self.messages
                if m.get("role") == "system"
                and not m.get("content", "").startswith("[Context:")
            ]
            self.messages = system[:1] if system else []
        else:
            self.messages = []

        # Reset counters
        self.compaction_count = 0

    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        return {
            "current_messages": len(self.messages),
            "total_processed": self.total_messages_processed,
            "compaction_count": self.compaction_count,
            "window_size": self.window_size,
            "strategy": self.strategy.value
        }

    def to_context_messages(self) -> List["Message"]:
        """Convert to TaskContext Message format."""
        from core.types import Message, MessageRole

        result = []
        for m in self.messages:
            role_str = m.get("role", "user")
            try:
                role = MessageRole(role_str)
            except ValueError:
                role = MessageRole.USER

            # Build metadata from extra fields
            metadata = {k: v for k, v in m.items() if k not in ("role", "content")}

            result.append(Message(
                role=role,
                content=m.get("content", ""),
                metadata=metadata
            ))

        return result

    def __len__(self) -> int:
        """Return number of messages."""
        return len(self.messages)

    def __repr__(self) -> str:
        """String representation."""
        return f"ConversationMemory(messages={len(self.messages)}, compactions={self.compaction_count})"


class MemoryManager:
    """Factory for creating memory instances.

    Supports different strategies based on use case.
    """

    @staticmethod
    def create(
        strategy: str = "simple",
        max_messages: int = 50,
        window_size: int = 20
    ) -> ConversationMemory:
        """Create a ConversationMemory instance.

        Args:
            strategy: "simple" or "summary"
            max_messages: Maximum messages before compaction
            window_size: Recent messages to keep in full

        Returns:
            Configured ConversationMemory instance
        """
        strat = CompactionStrategy.SIMPLE
        if strategy == "summary":
            strat = CompactionStrategy.SUMMARY
        elif strategy == "hybrid":
            strat = CompactionStrategy.HYBRID

        return ConversationMemory(
            max_messages=max_messages,
            window_size=window_size,
            compaction_threshold=int(max_messages * 0.8),
            strategy=strat
        )

    @staticmethod
    def from_config(config: Dict[str, Any]) -> ConversationMemory:
        """Create memory from config dict.

        Args:
            config: Config dict with memory settings

        Returns:
            Configured ConversationMemory instance
        """
        from core.utils import get_config_value

        memory_config = get_config_value(config, "memory") or {}

        return MemoryManager.create(
            strategy=memory_config.get("strategy", "simple"),
            max_messages=memory_config.get("max_messages", 50),
            window_size=memory_config.get("window_size", 20)
        )

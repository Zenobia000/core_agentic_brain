# Context & Memory Architecture Refactor Plan

**Version**: 1.0
**Date**: 2026-01-30
**Status**: Planning
**Priority**: P0 (Critical)

---

## 1. Executive Summary

### Problem Statement

當前系統在對話過程中缺乏上下文歷史紀錄。每次請求都是獨立的，沒有跨請求的記憶能力。

| 症狀 | 根因 |
|------|------|
| 每次請求獨立執行 | `main.py` 不維護會話記憶 |
| `ExecutorAgent` 每次重建 `local_messages` | 沒有使用 `context.messages` |
| `TaskContext.messages` 存在但沒人用 | 數據結構對，連接斷 |

### Solution Overview

採用 **三層記憶架構**，參考 Claude Code 和 OpenManus 的設計，用 Linus 風格簡化實現：

```
┌─────────────────────────────────────────────┐
│  Layer 1: Persistent (CLAUDE.md / config)   │ → 永久配置
├─────────────────────────────────────────────┤
│  Layer 2: Session (滑動窗口 + 自動摘要)      │ → 會話級記憶
├─────────────────────────────────────────────┤
│  Layer 3: Working (Tool outputs, 可丟棄)    │ → 即時工作記憶
└─────────────────────────────────────────────┘
```

---

## 2. Current State Analysis

### 2.1 Existing Data Structures

```python
# core/types.py - 結構存在
@dataclass
class TaskContext:
    prompt: str
    messages: List[Message] = field(default_factory=list)  # ← 未被使用
    tools: List[str] = field(default_factory=list)
    complexity: Optional[TaskComplexity] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    run_id: Optional[str] = None
    workspace_path: Optional[Path] = None

@dataclass
class Message:
    role: MessageRole  # USER, ASSISTANT, SYSTEM, TOOL
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: Optional[float] = None
```

### 2.2 Current Flow (Broken)

```
main.py                    kernel.py                  executor.py
   │                          │                          │
   │ execute(user_input)      │                          │
   ├─────────────────────────►│                          │
   │                          │ execute(request, context)│
   │                          ├─────────────────────────►│
   │                          │                          │
   │                          │      local_messages = [  │ ← 每次重建！
   │                          │        system_prompt,    │
   │                          │        context.prompt    │  context.messages
   │                          │      ]                   │  被忽略
   │                          │                          │
   │ result                   │                          │
   │◄─────────────────────────┤◄─────────────────────────┤
   │                          │                          │
   │ (歷史丟失)               │                          │
   ▼                          ▼                          ▼
```

### 2.3 Reference Architectures

#### Claude Code (4-Layer Memory)

| Layer | Purpose | Persistence |
|-------|---------|-------------|
| Enterprise Policy | Organization rules | Permanent |
| Project Memory (.claude.md) | Project instructions | Per-project |
| Session Context | Conversation + Compaction | Per-session |
| Working Memory | Tool outputs | Ephemeral |

**Key Features**:
- **Compaction**: Token 超限時自動生成摘要替換歷史
- **Subagent Isolation**: 子代理獨立上下文，只返回摘要
- **Checkpoint**: 每個 prompt 自動建立檢查點

#### OpenManus (Sliding Window + Summary)

| Component | Size | Strategy |
|-----------|------|----------|
| Active Window | Last 20 messages | Full retention |
| Archive | Compressed | LLM summarization |
| System Prompt | 1 message | Always preserved |

**Key Features**:
- `max_observe`: 截斷工具輸出
- `EnhancedMemory`: 兩層存儲 (active + archive)
- `MemoryOptimizer`: Token-aware 壓縮策略

---

## 3. Target Architecture

### 3.1 Three-Layer Memory Model

```
┌─────────────────────────────────────────────────────────────┐
│                    ConversationMemory                        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Layer 1: System Context (永久)                      │   │
│  │  - System prompt                                     │   │
│  │  - CLAUDE.md / config rules                         │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Layer 2: Session History (滑動窗口)                 │   │
│  │  - Recent N messages (default: 20)                  │   │
│  │  - Auto-compact when exceeds threshold              │   │
│  │  - Optional: LLM summarization for archive          │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Layer 3: Working Memory (即時)                      │   │
│  │  - Current tool calls & observations                │   │
│  │  - Cleared after each ReAct loop completion         │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Target Flow (Fixed)

```
main.py                    kernel.py                  executor.py
   │                          │                          │
   │ session_memory           │                          │
   │ (ConversationMemory)     │                          │
   │                          │                          │
   │ context = TaskContext(   │                          │
   │   prompt=user_input,     │                          │
   │   messages=session.get() │                          │
   │ )                        │                          │
   │                          │                          │
   │ execute(input, context)  │                          │
   ├─────────────────────────►│                          │
   │                          │ execute(request, context)│
   │                          ├─────────────────────────►│
   │                          │                          │
   │                          │      local_messages = [  │
   │                          │        system_prompt,    │
   │                          │        *context.messages,│ ← 使用歷史！
   │                          │        context.prompt    │
   │                          │      ]                   │
   │                          │                          │
   │ result                   │                          │
   │◄─────────────────────────┤◄─────────────────────────┤
   │                          │                          │
   │ session_memory.add(      │                          │
   │   user_input, result     │                          │
   │ )                        │                          │
   ▼                          ▼                          ▼
```

---

## 4. Implementation Plan

### 4.1 New File: `core/memory.py`

```python
"""
Conversation Memory Management
Linus: One data structure to rule them all.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum


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
            "content": content,
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
        # Separate system messages
        system_msgs = [m for m in self.messages if m.get("role") == "system"]
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
        """Compaction with LLM summary (requires async, placeholder)."""
        # For now, fall back to simple
        # TODO: Implement async LLM summarization
        self._compact_simple()

    def set_system_prompt(self, content: str) -> None:
        """Set or update system prompt (always first message)."""
        # Remove existing system prompts
        self.messages = [m for m in self.messages if m.get("role") != "system"
                        or m.get("content", "").startswith("[Context:")]

        # Insert system prompt at beginning
        self.messages.insert(0, {"role": "system", "content": content})

    def clear(self, keep_system: bool = True) -> None:
        """Clear memory, optionally keeping system prompt."""
        if keep_system:
            system = [m for m in self.messages if m.get("role") == "system"
                     and not m.get("content", "").startswith("[Context:")]
            self.messages = system[:1] if system else []
        else:
            self.messages = []

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

            result.append(Message(
                role=role,
                content=m.get("content", ""),
                metadata={k: v for k, v in m.items() if k not in ("role", "content")}
            ))

        return result


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
```

### 4.2 Modify: `main.py`

```python
# Add import
from core.memory import ConversationMemory

async def interactive_mode(kernel: Kernel):
    """互動模式 - CLI 介面"""
    # ... existing banner code ...

    # Initialize session memory
    session_memory = ConversationMemory(
        max_messages=50,
        window_size=20
    )

    while True:
        try:
            user_input = input(">>> ").strip()

            # ... existing command handling ...

            # Create context with history
            context = TaskContext(
                prompt=user_input,
                messages=session_memory.to_context_messages()
            )

            # Handle clarification...
            print(f"\n🔄 處理中...")
            result = await kernel.execute(user_input, context)

            # Handle CLARIFICATION_NEEDED...
            if result.error == "CLARIFICATION_NEEDED":
                # ... existing clarification handling ...
                pass

            # Save to session memory
            session_memory.add("user", user_input)
            if result.success:
                session_memory.add("assistant", result.response)

            # Display results...
            # ... existing display code ...

            # Show memory stats (optional, for debugging)
            stats = session_memory.get_stats()
            if stats["compaction_count"] > 0:
                print(f"📊 Memory: {stats['current_messages']} msgs, {stats['compaction_count']} compactions")

        except KeyboardInterrupt:
            # ... existing handling ...
```

### 4.3 Modify: `agents/executor.py`

```python
async def _execute_react(self, context: TaskContext) -> ExecutionResult:
    """Execute task using internal ReAct loop."""
    # ... existing setup code ...

    # Build initial message history - USE CONTEXT MESSAGES
    local_messages: List[Dict[str, Any]] = [
        {"role": "system", "content": self.get_system_prompt()}
    ]

    # Add history from context (NEW)
    for msg in context.messages:
        if msg.role.value == "system":
            continue  # Skip system messages from history (we have our own)
        local_messages.append({
            "role": msg.role.value,
            "content": msg.content,
            **msg.metadata  # Include tool_calls, tool_call_id, etc.
        })

    # Add current prompt
    local_messages.append({"role": "user", "content": context.prompt})

    # ... rest of existing ReAct loop ...
```

### 4.4 Configuration: `config.yaml`

```yaml
# Memory configuration (add to config.yaml)
memory:
  strategy: simple          # simple, summary, hybrid
  max_messages: 50          # Total max before compaction
  window_size: 20           # Recent messages to keep
  enable_stats: false       # Show memory stats in CLI
```

---

## 5. Implementation Checklist

### Phase 1: Core Memory (P0)

- [ ] Create `core/memory.py` with `ConversationMemory` class
- [ ] Add unit tests for memory operations
- [ ] Add memory config to `config.yaml`

### Phase 2: Integration (P0)

- [ ] Modify `main.py` to use `ConversationMemory`
- [ ] Modify `ExecutorAgent._execute_react()` to use `context.messages`
- [ ] Test end-to-end conversation flow

### Phase 3: Enhancement (P1)

- [ ] Implement LLM-based summarization for `CompactionStrategy.SUMMARY`
- [ ] Add `/memory` command to show stats in CLI
- [ ] Add `/clear` command to reset session memory

### Phase 4: Advanced (P2)

- [ ] Tool masking (instead of removal)
- [ ] Checkpoint system for conversation rollback
- [ ] Subagent context isolation

---

## 6. Testing Plan

### Unit Tests

```python
# tests/test_memory.py

def test_memory_add():
    """Test basic message addition."""
    mem = ConversationMemory()
    mem.add("user", "Hello")
    mem.add("assistant", "Hi there")
    assert len(mem.messages) == 2

def test_memory_compaction():
    """Test auto-compaction at threshold."""
    mem = ConversationMemory(max_messages=10, window_size=5, compaction_threshold=8)
    for i in range(10):
        mem.add("user", f"Message {i}")

    assert len(mem.messages) <= 10
    assert mem.compaction_count >= 1

def test_memory_system_prompt():
    """Test system prompt handling."""
    mem = ConversationMemory()
    mem.set_system_prompt("You are helpful.")
    mem.add("user", "Hello")

    assert mem.messages[0]["role"] == "system"
    assert mem.messages[0]["content"] == "You are helpful."
```

### Integration Tests

```python
# tests/test_memory_integration.py

async def test_conversation_history():
    """Test that conversation history is passed to executor."""
    kernel = Kernel()
    memory = ConversationMemory()

    # First turn
    memory.add("user", "My name is Alice")
    context1 = TaskContext(prompt="My name is Alice", messages=memory.to_context_messages())
    result1 = await kernel.execute("My name is Alice", context1)
    memory.add("assistant", result1.response)

    # Second turn - should remember the name
    memory.add("user", "What is my name?")
    context2 = TaskContext(prompt="What is my name?", messages=memory.to_context_messages())
    result2 = await kernel.execute("What is my name?", context2)

    assert "Alice" in result2.response
```

---

## 7. Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Token usage increase | Medium | Compaction + window size limits |
| Memory leak in long sessions | High | Max messages + periodic clear |
| LLM confusion from too much history | Medium | Summarization for old messages |
| Breaking changes to existing flow | Low | Backward compatible (messages optional) |

---

## 8. References

### External Sources

- [How Claude Code works](https://code.claude.com/docs/en/how-claude-code-works)
- [Claude Code: Conversation Management and Context](https://www.letanure.dev/blog/2025-08-01--claude-code-part-3-conversation-management-context)
- [Context editing - Claude API](https://platform.claude.com/docs/en/build-with-claude/context-editing)
- [Cursor AI Complete Guide 2025](https://medium.com/@hilalkara.dev/cursor-ai-complete-guide-2025-real-experiences-pro-tips-mcps-rules-context-engineering-6de1a776a8af)
- [Cursor Context Documentation](https://cursor.com/learn/context)

### Internal Documents

- `docs/預期開發架構/Context_Engineering_Analysis_Report.md`
- `legacy/OpenManus/` - Reference implementation

---

## 9. Appendix: Message Flow Diagram

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         Conversation Flow                                 │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  User Input                                                              │
│      │                                                                   │
│      ▼                                                                   │
│  ┌─────────────────┐                                                     │
│  │ ConversationMemory │◄──── Session-level persistence                   │
│  │  .add(user, input) │                                                  │
│  └────────┬────────┘                                                     │
│           │                                                              │
│           ▼                                                              │
│  ┌─────────────────┐                                                     │
│  │   TaskContext    │                                                    │
│  │  prompt: input   │                                                    │
│  │  messages: [...]◄├──── History from memory                            │
│  └────────┬────────┘                                                     │
│           │                                                              │
│           ▼                                                              │
│  ┌─────────────────┐                                                     │
│  │     Kernel       │                                                    │
│  │   .execute()     │                                                    │
│  └────────┬────────┘                                                     │
│           │                                                              │
│           ▼                                                              │
│  ┌─────────────────┐     ┌─────────────────┐                            │
│  │  ExecutorAgent   │────►│  local_messages  │                           │
│  │ ._execute_react()│     │  [system,        │                           │
│  └────────┬────────┘     │   ...history,    │                           │
│           │              │   current]       │                           │
│           │              └─────────────────┘                            │
│           ▼                                                              │
│  ┌─────────────────┐                                                     │
│  │   LLM Call       │                                                    │
│  │  (with history)  │                                                    │
│  └────────┬────────┘                                                     │
│           │                                                              │
│           ▼                                                              │
│  ┌─────────────────┐                                                     │
│  │ ExecutionResult  │                                                    │
│  └────────┬────────┘                                                     │
│           │                                                              │
│           ▼                                                              │
│  ┌─────────────────┐                                                     │
│  │ ConversationMemory │                                                  │
│  │  .add(assistant,   │                                                  │
│  │       response)    │                                                  │
│  └─────────────────┘                                                     │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

**Document History**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-30 | AI Architect | Initial draft |

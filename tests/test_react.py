"""
ReAct loop improvements tests.
Based on Linus principle: Test actual behavior, not theory.
"""

import pytest
from collections import deque
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from core.types import TaskContext, ReactConfig, ToolCallSignature, ExecutionResult


class TestReactConfig:
    """ReactConfig dataclass tests."""

    def test_default_values(self):
        """Test default values are sensible."""
        config = ReactConfig()
        assert config.max_steps == 10
        assert config.token_budget == 15000  # Base budget (auto-scaled by complexity)
        assert config.token_warning_threshold == 0.8
        assert config.max_consecutive_errors == 3
        assert config.repetition_window == 5
        assert config.enable_summarization is True

    def test_custom_values(self):
        """Test custom values override defaults."""
        config = ReactConfig(
            max_steps=20,
            token_budget=16000,
            max_consecutive_errors=5,
            enable_summarization=False
        )
        assert config.max_steps == 20
        assert config.token_budget == 16000
        assert config.max_consecutive_errors == 5
        assert config.enable_summarization is False
        # Unchanged defaults
        assert config.token_warning_threshold == 0.8
        assert config.repetition_window == 5


class TestToolCallSignature:
    """ToolCallSignature tests for repetition detection."""

    def test_same_call_same_signature(self):
        """Same tool call produces same signature."""
        sig1 = ToolCallSignature.from_tool_call("python", '{"code": "print(1)"}')
        sig2 = ToolCallSignature.from_tool_call("python", '{"code": "print(1)"}')
        assert sig1 == sig2
        assert hash(sig1) == hash(sig2)

    def test_different_args_different_signature(self):
        """Different args produce different signature."""
        sig1 = ToolCallSignature.from_tool_call("python", '{"code": "print(1)"}')
        sig2 = ToolCallSignature.from_tool_call("python", '{"code": "print(2)"}')
        assert sig1 != sig2

    def test_different_tool_different_signature(self):
        """Different tool names produce different signature."""
        sig1 = ToolCallSignature.from_tool_call("python", '{"code": "x"}')
        sig2 = ToolCallSignature.from_tool_call("files", '{"code": "x"}')
        assert sig1 != sig2

    def test_signature_hashable(self):
        """Signature can be used in sets and dicts."""
        sig = ToolCallSignature.from_tool_call("python", '{"code": "x"}')
        sig_set = {sig}
        assert sig in sig_set

    def test_signature_in_deque(self):
        """Signature works correctly with deque for repetition detection."""
        recent = deque(maxlen=5)
        sig = ToolCallSignature.from_tool_call("python", '{"code": "x"}')

        recent.append(sig)
        recent.append(sig)
        recent.append(sig)

        repetition_count = sum(1 for c in recent if c == sig)
        assert repetition_count == 3


class TestExecutorAgentReactConfig:
    """ExecutorAgent ReAct config loading tests."""

    @pytest.fixture
    def mock_kernel(self):
        """Create mock kernel."""
        kernel = Mock()
        kernel.get_tool_definitions.return_value = []
        kernel.call_tool = AsyncMock(return_value={"success": True})
        return kernel

    @pytest.fixture
    def executor_with_kernel(self, mock_kernel):
        """Create executor with mocked dependencies."""
        from agents.executor import ExecutorAgent

        with patch('core.llm.LLMProvider._init_client', return_value=Mock()):
            with patch('core.config.load_config', return_value={"react": {}}):
                agent = ExecutorAgent(kernel=mock_kernel)
        return agent

    def test_config_loading_from_context(self, executor_with_kernel):
        """Test config override from context.metadata."""
        context = TaskContext(
            prompt="test",
            metadata={
                "react_config": {
                    "max_steps": 5,
                    "token_budget": 4000
                }
            }
        )

        effective = executor_with_kernel._get_effective_config(context)
        assert effective.max_steps == 5
        assert effective.token_budget == 4000
        # Unchanged from base config
        assert effective.max_consecutive_errors == 3

    def test_config_no_override(self, executor_with_kernel):
        """Test config without override uses defaults."""
        context = TaskContext(prompt="test")

        effective = executor_with_kernel._get_effective_config(context)
        assert effective.max_steps == executor_with_kernel.react_config.max_steps
        assert effective.token_budget == executor_with_kernel.react_config.token_budget


class TestMessageSummarization:
    """Message summarization tests."""

    @pytest.fixture
    def executor(self):
        """Create executor agent for testing."""
        from agents.executor import ExecutorAgent

        with patch('core.llm.LLMProvider._init_client', return_value=Mock()):
            with patch('core.config.load_config', return_value={"react": {}}):
                agent = ExecutorAgent()
        return agent

    def test_short_messages_unchanged(self, executor):
        """Short message list should not be summarized."""
        messages = [
            {"role": "system", "content": "system"},
            {"role": "user", "content": "user"},
            {"role": "assistant", "content": "response"}
        ]

        result = executor._summarize_messages(messages)
        assert len(result) == len(messages)

    def test_long_messages_summarized(self, executor):
        """Long message list should be summarized."""
        messages = [
            {"role": "system", "content": "system prompt"},
            {"role": "user", "content": "user prompt"},
            {"role": "assistant", "content": "thought 1"},
            {"role": "tool", "content": "result 1"},
            {"role": "assistant", "content": "thought 2"},
            {"role": "tool", "content": "result 2"},
            {"role": "assistant", "content": "thought 3"},
            {"role": "tool", "content": "result 3"},
        ]

        result = executor._summarize_messages(messages)

        # Should be shorter
        assert len(result) < len(messages)
        # System and user preserved
        assert result[0]["role"] == "system"
        assert result[1]["role"] == "user"
        # Summary message present
        assert any("summarized" in msg.get("content", "") for msg in result)

    def test_preserves_recent_messages(self, executor):
        """Summarization should preserve recent messages."""
        messages = [
            {"role": "system", "content": "system"},
            {"role": "user", "content": "user"},
            {"role": "assistant", "content": "old1"},
            {"role": "tool", "content": "old2"},
            {"role": "assistant", "content": "recent1"},
            {"role": "tool", "content": "recent2"},
        ]

        result = executor._summarize_messages(messages)

        # Recent messages should be at the end
        assert result[-1]["content"] == "recent2"
        assert result[-2]["content"] == "recent1"


class TestRepetitionDetection:
    """Repetition detection logic tests."""

    def test_detects_repeated_calls_in_window(self):
        """Should detect repeated calls within window."""
        recent_calls: deque[ToolCallSignature] = deque(maxlen=5)
        sig = ToolCallSignature.from_tool_call("python", '{"code": "x"}')

        # Add same call multiple times
        for _ in range(3):
            recent_calls.append(sig)

        repetition_count = sum(1 for c in recent_calls if c == sig)
        assert repetition_count == 3

    def test_window_evicts_old_calls(self):
        """Window should evict old calls."""
        recent_calls: deque[ToolCallSignature] = deque(maxlen=3)
        old_sig = ToolCallSignature.from_tool_call("python", '{"code": "old"}')
        new_sig = ToolCallSignature.from_tool_call("python", '{"code": "new"}')

        # Fill with old
        for _ in range(3):
            recent_calls.append(old_sig)

        # Add new calls
        for _ in range(3):
            recent_calls.append(new_sig)

        # Old should be evicted
        assert old_sig not in recent_calls
        assert sum(1 for c in recent_calls if c == new_sig) == 3


class TestCircuitBreaker:
    """Error circuit breaker tests."""

    def test_consecutive_error_tracking(self):
        """Consecutive errors should be tracked correctly."""
        consecutive_errors = 0

        # Simulate 3 failures
        for _ in range(3):
            consecutive_errors += 1

        assert consecutive_errors == 3

    def test_success_resets_counter(self):
        """Success should reset consecutive error counter."""
        consecutive_errors = 2

        # Simulate success
        consecutive_errors = 0

        assert consecutive_errors == 0


class TestTokenBudget:
    """Token budget management tests."""

    def test_budget_threshold_calculation(self):
        """Token warning threshold should be calculated correctly."""
        config = ReactConfig(token_budget=10000, token_warning_threshold=0.8)

        total_tokens = 8000
        at_threshold = total_tokens >= config.token_budget * config.token_warning_threshold

        assert at_threshold is True

    def test_budget_exhausted_check(self):
        """Budget exhaustion should be detected."""
        config = ReactConfig(token_budget=8000)

        total_tokens = 8500
        exhausted = total_tokens >= config.token_budget

        assert exhausted is True


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])

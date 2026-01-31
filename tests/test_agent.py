# tests/test_agent.py
"""
DEPRECATED: Tests for the old core/agent.py which has been removed.

The old Agent class has been replaced by the OKR-based architecture:
- core/kernel.py - Orchestration hub
- agents/executor.py - ReAct execution with OKR goals
- agents/planner.py - Planning agent
- agents/reviewer.py - OKR checklist validation

See tests/test_kernel.py for new architecture tests.
"""
import pytest

pytestmark = pytest.mark.skip(reason="Old core/agent.py removed. Use Kernel-based architecture.")


def test_placeholder():
    """Placeholder to prevent empty test file errors."""
    pass

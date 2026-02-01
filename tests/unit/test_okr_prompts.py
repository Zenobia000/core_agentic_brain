#!/usr/bin/env python3
"""
OKR Prompt Integration Tests

Tests for OKR-based prompt loading and usage:
- Prompt loader loading OKR prompts
- Agent prompt building with OKR
- OKR prompt variable substitution
"""

import pytest
from core.prompt_loader import get_prompt_loader
from core.types import TaskContext


class TestOKRPromptLoading:
    """Test OKR prompt loading from YAML files."""

    @pytest.fixture
    def loader(self):
        """Get prompt loader instance."""
        return get_prompt_loader()

    def test_router_prompts_exist(self, loader):
        """Test router prompts are loaded."""
        system = loader.get("router.system")
        refine = loader.get("router.refine_query")

        assert system is not None
        assert len(system) > 0
        assert refine is not None
        assert len(refine) > 0

    def test_planner_okr_prompt_exists(self, loader):
        """Test planner OKR prompt exists."""
        planning_okr = loader.get("planner.planning_okr")

        assert planning_okr is not None
        assert "{okr_prompt}" in planning_okr
        assert "{task}" in planning_okr

    def test_planner_fallback_prompt_exists(self, loader):
        """Test planner fallback prompt exists."""
        planning = loader.get("planner.planning")

        assert planning is not None
        assert "{task}" in planning

    def test_reviewer_okr_prompt_exists(self, loader):
        """Test reviewer OKR prompt exists."""
        review_okr = loader.get("reviewer.review_okr")

        assert review_okr is not None
        assert "{okr_prompt}" in review_okr
        assert "{result}" in review_okr

    def test_reviewer_fallback_prompt_exists(self, loader):
        """Test reviewer fallback prompt exists."""
        review = loader.get("reviewer.review")

        assert review is not None
        assert "{task}" in review
        assert "{result}" in review

    def test_executor_system_prompt(self, loader):
        """Test executor system prompt has OKR references."""
        system = loader.get("executor.system")

        assert system is not None
        # Should reference OKR concepts
        assert "Key Result" in system or "OKR" in system or "checklist" in system.lower()


class TestOKRPromptFormatting:
    """Test OKR prompt variable substitution."""

    @pytest.fixture
    def loader(self):
        """Get prompt loader instance."""
        return get_prompt_loader()

    def test_planner_okr_formatting(self, loader):
        """Test planner OKR prompt formatting."""
        template = loader.get("planner.planning_okr")

        okr_content = """## OBJECTIVE
Test objective

## KEY RESULTS
- [ ] Item 1
- [ ] Item 2"""

        formatted = template.format(
            okr_prompt=okr_content,
            task="Test task"
        )

        assert "Test objective" in formatted
        assert "Item 1" in formatted
        assert "Test task" in formatted

    def test_reviewer_okr_formatting(self, loader):
        """Test reviewer OKR prompt formatting."""
        template = loader.get("reviewer.review_okr")

        okr_content = """## KEY RESULTS
- [ ] Requirement met"""

        formatted = template.format(
            okr_prompt=okr_content,
            result="Task completed successfully"
        )

        assert "Requirement met" in formatted
        assert "Task completed successfully" in formatted

    def test_router_refine_formatting(self, loader):
        """Test router refine query formatting."""
        template = loader.get("router.refine_query")

        # Router now includes domain selection, needs available_domains
        formatted = template.format(
            prompt="Plan a trip to Tokyo",
            available_domains="- travel_planning: hints=[旅遊, travel]"
        )

        assert "Plan a trip to Tokyo" in formatted
        assert "intent_type" in formatted.lower()
        assert "domain" in formatted.lower()  # New: domain selection


class TestOKRPromptFlow:
    """Test the complete OKR prompt flow."""

    @pytest.fixture
    def loader(self):
        """Get prompt loader instance."""
        return get_prompt_loader()

    @pytest.fixture
    def sample_okr(self):
        """Sample OKR content."""
        return """## OBJECTIVE
Create a working solution

## KEY RESULTS (Must be achieved)

### Requirements
- [ ] Functionality defined
- [ ] Constraints identified

### Implementation
- [ ] Code is runnable
- [ ] No hardcoded secrets

## CONSTRAINTS
- Never break existing functionality
- Always include error handling

## SUCCESS CRITERIA
APPROVED only if ALL checklist items satisfied"""

    def test_planner_receives_okr(self, loader, sample_okr):
        """Test planner prompt includes OKR."""
        template = loader.get("planner.planning_okr")
        formatted = template.format(okr_prompt=sample_okr, task="Build feature X")

        # Verify OKR structure is preserved
        assert "OBJECTIVE" in formatted
        assert "KEY RESULTS" in formatted
        assert "Requirements" in formatted
        assert "Implementation" in formatted
        assert "CONSTRAINTS" in formatted

    def test_reviewer_receives_okr(self, loader, sample_okr):
        """Test reviewer prompt includes OKR for validation."""
        template = loader.get("reviewer.review_okr")
        formatted = template.format(
            okr_prompt=sample_okr,
            result="Feature X implemented with all requirements"
        )

        # Verify OKR is included for validation
        assert "OBJECTIVE" in formatted
        assert "KEY RESULTS" in formatted
        assert "Feature X implemented" in formatted

    def test_context_metadata_okr_injection(self):
        """Test framework guidance is correctly placed in context metadata."""
        from core.schema import detect_schema

        context = TaskContext(prompt="規劃旅遊")
        schema = detect_schema(context.prompt)

        if schema:
            context.metadata["domain_schema"] = schema.domain
            context.metadata["okr_prompt"] = schema.get_okr_prompt()

        assert "okr_prompt" in context.metadata
        # New 4-element framework structure (replaces OKR)
        assert "CONTEXT" in context.metadata["okr_prompt"]
        assert "GAP" in context.metadata["okr_prompt"]
        assert "CONSTRAINTS" in context.metadata["okr_prompt"]
        assert "DELIVERABLE" in context.metadata["okr_prompt"]


class TestOKRPromptConsistency:
    """Test consistency between prompts and schemas."""

    def test_prompts_reference_okr_consistently(self):
        """Test all OKR prompts use consistent variable names."""
        loader = get_prompt_loader()

        # All OKR prompts should use {okr_prompt}
        planning_okr = loader.get("planner.planning_okr")
        review_okr = loader.get("reviewer.review_okr")

        assert "{okr_prompt}" in planning_okr
        assert "{okr_prompt}" in review_okr

    def test_fallback_prompts_dont_require_okr(self):
        """Test fallback prompts work without OKR."""
        loader = get_prompt_loader()

        # Fallback prompts should not require okr_prompt
        planning = loader.get("planner.planning")
        review = loader.get("reviewer.review")

        assert "{okr_prompt}" not in planning
        assert "{okr_prompt}" not in review

        # Should be formattable without okr_prompt
        planning.format(task="test", system2_context="", tools="search")
        review.format(task="test", result="done")

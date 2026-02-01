#!/usr/bin/env python3
"""
Framework End-to-End Integration Tests

Tests the complete framework flow:
Router (domain selection) → Kernel (framework inject) → Planner → Executor → Reviewer

Architecture:
- Universal 4-element framework (CONTEXT/GAP/CONSTRAINTS/DELIVERABLE)
- Hot-pluggable domain expertise (schemas/domains/*.yaml)
- LLM-based domain selection (no keyword matching)

These tests verify the architecture without requiring actual LLM calls.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from core.types import TaskContext, ExecutionResult, RoutingDecision, TaskComplexity, AgentRole
from core.schema import (
    detect_schema, reset_schema_loader, reset_framework_loader,
    get_problem_framework, get_domain_expertise, get_framework_loader
)
from core.prompt_loader import get_prompt_loader


class TestFrameworkDetectionFlow:
    """Test framework detection at various stages."""

    @pytest.fixture(autouse=True)
    def reset(self):
        """Reset schema loader."""
        reset_framework_loader()
        yield
        reset_framework_loader()

    def test_universal_framework_always_returned(self):
        """Test universal framework is always returned (no keyword matching)."""
        prompts = [
            "規劃京都旅行",
            "plan a trip to Tokyo",
            "寫一個排序函數",
            "random task without domain"
        ]

        for prompt in prompts:
            schema = detect_schema(prompt)
            assert schema is not None, f"Schema should always be returned for: {prompt}"
            # New architecture: always returns "universal"
            assert schema.domain == "universal", f"Should be universal for: {prompt}"

    def test_framework_has_four_elements(self):
        """Test framework contains all four elements."""
        framework = get_problem_framework()

        assert "CONTEXT" in framework
        assert "GAP" in framework
        assert "CONSTRAINTS" in framework
        assert "DELIVERABLE" in framework

    def test_framework_injection_to_context(self):
        """Test framework is correctly injected into context metadata."""
        context = TaskContext(prompt="規劃旅遊行程")
        schema = detect_schema(context.prompt)

        assert schema is not None

        # Simulate kernel injection
        context.metadata["domain_schema"] = schema.domain
        context.metadata["okr_prompt"] = schema.get_okr_prompt()

        # Verify injection
        assert context.metadata["domain_schema"] == "universal"
        # New 4-element framework structure
        assert "CONTEXT" in context.metadata["okr_prompt"]
        assert "GAP" in context.metadata["okr_prompt"]
        assert "CONSTRAINTS" in context.metadata["okr_prompt"]
        assert "DELIVERABLE" in context.metadata["okr_prompt"]


class TestDomainExpertise:
    """Test hot-pluggable domain expertise."""

    @pytest.fixture(autouse=True)
    def reset(self):
        """Reset framework loader."""
        reset_framework_loader()
        yield
        reset_framework_loader()

    def test_domain_expertise_loading(self):
        """Test domain expertise files are loaded correctly."""
        loader = get_framework_loader()
        domains = loader.list_domains()

        # Should have at least travel and software domains
        assert "travel_planning" in domains
        assert "software_development" in domains

    def test_domain_expertise_content(self):
        """Test domain expertise has meaningful content."""
        travel = get_domain_expertise("travel_planning")
        software = get_domain_expertise("software_development")

        assert travel is not None
        assert len(travel) > 100  # Should be substantial content

        assert software is not None
        assert len(software) > 100

    def test_nonexistent_domain_returns_none(self):
        """Test nonexistent domain returns None gracefully."""
        result = get_domain_expertise("definitely_not_a_domain")
        assert result is None

    def test_framework_combined_with_domain(self):
        """Test framework + domain expertise combination."""
        schema = detect_schema("any query")
        guidance = schema.get_guidance()

        # Should have framework
        assert "CONTEXT" in guidance
        assert "GAP" in guidance
        assert "CONSTRAINTS" in guidance
        assert "DELIVERABLE" in guidance


class TestPromptBuilding:
    """Test prompt building with framework."""

    @pytest.fixture
    def context_with_framework(self):
        """Create a context with framework."""
        context = TaskContext(prompt="規劃京都4天3夜旅行")
        schema = detect_schema(context.prompt)
        if schema:
            context.metadata["domain_schema"] = schema.domain
            context.metadata["okr_prompt"] = schema.get_okr_prompt()
        return context

    def test_planner_uses_framework_prompt(self, context_with_framework):
        """Test planner builds prompt with framework."""
        loader = get_prompt_loader()

        okr_prompt = context_with_framework.metadata.get("okr_prompt")
        assert okr_prompt is not None

        template = loader.get("planner.planning_okr")
        prompt = template.format(
            okr_prompt=okr_prompt,
            task=context_with_framework.prompt
        )

        # Verify 4-element framework content is in the prompt
        assert "CONTEXT" in prompt or "GAP" in prompt
        assert "京都" in prompt or "旅行" in prompt

    def test_reviewer_uses_framework_prompt(self, context_with_framework):
        """Test reviewer builds prompt with framework."""
        loader = get_prompt_loader()

        okr_prompt = context_with_framework.metadata.get("okr_prompt")
        assert okr_prompt is not None

        template = loader.get("reviewer.review_okr")
        prompt = template.format(
            okr_prompt=okr_prompt,
            result="Plan completed"
        )

        # Verify framework content is in the prompt
        assert len(prompt) > 100


class TestRouterWithMocks:
    """Test complete router flow with mocked LLM."""

    @pytest.fixture
    def mock_llm_response(self):
        """Create mock LLM response with domain selection."""
        mock = AsyncMock()
        mock.generate = AsyncMock(return_value=MagicMock(
            content='{"intent_type": "planning", "domain": "travel_planning", "ambiguity_level": "low", "refined_goal": "Plan trip"}'
        ))
        return mock

    @pytest.mark.asyncio
    async def test_router_analysis_with_domain(self, mock_llm_response):
        """Test router correctly identifies domain."""
        from router.llm_analyzer import LLMTaskAnalyzer

        analyzer = LLMTaskAnalyzer(llm_provider=mock_llm_response)
        context = TaskContext(prompt="規劃京都旅行")

        decision = await analyzer.analyze(context)

        assert decision is not None
        assert hasattr(decision, 'strategy')
        assert hasattr(decision, 'agents')
        # Should have domain and okr_prompt in metadata
        assert "domain" in decision.metadata
        assert "okr_prompt" in decision.metadata

    @pytest.mark.asyncio
    async def test_router_injects_framework(self):
        """Test router injects framework into context via metadata."""
        # Create context
        context = TaskContext(prompt="規劃旅遊")

        # Simulate what orchestration.py does
        schema = detect_schema(context.prompt)
        if schema:
            context.metadata["domain_schema"] = schema.domain
            context.metadata["okr_prompt"] = schema.get_okr_prompt()

        # Verify framework was injected
        assert "domain_schema" in context.metadata
        assert context.metadata["domain_schema"] == "universal"
        assert "okr_prompt" in context.metadata
        assert len(context.metadata["okr_prompt"]) > 100  # Should be substantial


class TestFrameworkValidation:
    """Test framework validation logic."""

    def test_framework_has_required_elements(self):
        """Test framework has all required elements."""
        framework = get_problem_framework()

        # Required elements for 4-element framework
        required = ["CONTEXT", "GAP", "CONSTRAINTS", "DELIVERABLE"]
        for element in required:
            assert element in framework, f"Missing element: {element}"

    def test_framework_has_analysis_process(self):
        """Test framework has analysis process description."""
        framework = get_problem_framework()

        # Should describe the analysis process
        assert "Extract" in framework or "extract" in framework
        assert "KNOWN" in framework or "UNKNOWN" in framework


class TestAgentFrameworkIntegration:
    """Test agent integration with framework."""

    @pytest.fixture
    def context_with_framework(self):
        """Create context with framework injected."""
        context = TaskContext(prompt="規劃日本旅行")
        schema = detect_schema(context.prompt)
        if schema:
            context.metadata["domain_schema"] = schema.domain
            context.metadata["okr_prompt"] = schema.get_okr_prompt()
        return context

    def test_planner_prompt_selection(self, context_with_framework):
        """Test planner selects framework prompt when available."""
        # Simulate planner's _build_planning_prompt logic
        okr_prompt = context_with_framework.metadata.get("okr_prompt")

        if okr_prompt:
            # Should use planning_okr
            loader = get_prompt_loader()
            template = loader.get("planner.planning_okr")
            prompt = template.format(okr_prompt=okr_prompt, task=context_with_framework.prompt)
        else:
            pytest.fail("Framework should be present")

        # New 4-element framework
        assert "CONTEXT" in prompt or "GAP" in prompt or "CONSTRAINTS" in prompt
        assert "日本" in prompt or "旅行" in prompt

    def test_reviewer_prompt_selection(self, context_with_framework):
        """Test reviewer selects framework prompt when available."""
        okr_prompt = context_with_framework.metadata.get("okr_prompt")

        if okr_prompt:
            loader = get_prompt_loader()
            template = loader.get("reviewer.review_okr")
            prompt = template.format(okr_prompt=okr_prompt, result="Plan completed")
        else:
            pytest.fail("Framework should be present")

        assert "Plan completed" in prompt
        assert len(prompt) > 100

    def test_executor_receives_framework_in_context(self, context_with_framework):
        """Test executor can access framework from context."""
        # Executor should be able to access framework
        assert "okr_prompt" in context_with_framework.metadata

        okr = context_with_framework.metadata["okr_prompt"]

        # Should have 4-element framework
        assert "CONTEXT" in okr
        assert "GAP" in okr
        assert "CONSTRAINTS" in okr
        assert "DELIVERABLE" in okr


class TestClarificationGate:
    """Test clarification gate in router (Phase 6)."""

    def test_clarification_decision_structure(self):
        """Test that clarification routing decision has correct structure."""
        from router.llm_analyzer import LLMTaskAnalyzer
        from core.types import TaskComplexity

        analyzer = LLMTaskAnalyzer()

        # Simulate high ambiguity refinement result
        refinement = {
            "intent_type": "planning",
            "domain": "none",
            "ambiguity_level": "high",
            "key_questions": ["What is the budget?", "How many days?", "What destinations?"],
            "refined_goal": "Plan a trip",
            "thought_process": "User wants travel planning but missing key details"
        }

        context = TaskContext(prompt="Plan a trip")

        # Check clarification decision
        decision = analyzer._check_clarification_needed(refinement, context)

        assert decision is not None, "Should return clarification decision for high ambiguity"
        assert decision.strategy == "clarification"
        assert decision.agents == []
        assert decision.complexity == TaskComplexity.SIMPLE
        assert "key_questions" in decision.metadata
        assert len(decision.metadata["key_questions"]) <= 3

    def test_no_clarification_for_low_ambiguity(self):
        """Test that low ambiguity doesn't trigger clarification."""
        from router.llm_analyzer import LLMTaskAnalyzer

        analyzer = LLMTaskAnalyzer()

        refinement = {
            "intent_type": "simple_query",
            "domain": "none",
            "ambiguity_level": "low",
            "key_questions": [],
            "refined_goal": "What is 2+2?",
        }

        context = TaskContext(prompt="What is 2+2?")
        decision = analyzer._check_clarification_needed(refinement, context)

        assert decision is None, "Should not trigger clarification for low ambiguity"

    def test_clarification_skipped_when_provided(self):
        """Test that clarification is skipped if already provided."""
        from router.llm_analyzer import LLMTaskAnalyzer

        analyzer = LLMTaskAnalyzer()

        refinement = {
            "domain": "none",
            "ambiguity_level": "high",
            "key_questions": ["What is the budget?"],
        }

        # Context with clarification already provided
        context = TaskContext(prompt="Plan trip with $1000 budget")
        context.metadata["clarification_provided"] = True

        decision = analyzer._check_clarification_needed(refinement, context)

        assert decision is None, "Should skip clarification when already provided"


class TestFrameworkFallback:
    """Test fallback behavior."""

    def test_universal_framework_always_available(self):
        """Test universal framework is always returned."""
        context = TaskContext(prompt="random task without domain")

        schema = detect_schema(context.prompt)
        # New architecture: universal framework always returned
        assert schema is not None
        assert schema.domain == "universal"

        # Framework should have content
        guidance = schema.get_guidance()
        assert "CONTEXT" in guidance
        assert "GAP" in guidance

    def test_planner_fallback_without_domain_expertise(self):
        """Test planner uses framework even without specific domain."""
        context = TaskContext(prompt="random task without domain")

        schema = detect_schema(context.prompt)
        assert schema is not None

        # Should still have framework content
        okr_prompt = schema.get_okr_prompt()
        assert "CONTEXT" in okr_prompt
        assert "GAP" in okr_prompt
        assert "CONSTRAINTS" in okr_prompt
        assert "DELIVERABLE" in okr_prompt

    def test_reviewer_fallback_without_domain_expertise(self):
        """Test reviewer uses fallback when no OKR."""
        context = TaskContext(prompt="unknown task type")

        loader = get_prompt_loader()
        template = loader.get("reviewer.review")

        prompt = template.format(
            task=context.prompt,
            result="Task completed"
        )

        assert "unknown task type" in prompt
        assert "Task completed" in prompt


class TestRoutingPrompt:
    """Test routing prompt generation."""

    @pytest.fixture(autouse=True)
    def reset(self):
        """Reset framework loader."""
        reset_framework_loader()
        yield
        reset_framework_loader()

    def test_routing_prompt_includes_domains(self):
        """Test routing prompt includes available domains."""
        loader = get_framework_loader()
        routing_prompt = loader.get_routing_prompt()

        # Should include available domains
        assert "travel_planning" in routing_prompt
        assert "software_development" in routing_prompt

    def test_routing_prompt_includes_hints(self):
        """Test routing prompt includes domain hints."""
        loader = get_framework_loader()
        routing_prompt = loader.get_routing_prompt()

        # Should include hints from domain files
        assert "hints" in routing_prompt.lower()

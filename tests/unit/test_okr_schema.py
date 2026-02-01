#!/usr/bin/env python3
"""
Universal Problem Framework Tests

Tests for the universal problem-solving framework:
- Framework loading
- Domain expertise injection
- Backward compatibility
"""

import pytest
from core.schema import (
    UniversalFramework,
    DomainExpertise,
    FrameworkLoader,
    get_framework_loader,
    get_problem_framework,
    get_domain_expertise,
    reset_framework_loader,
    # Backward compatibility
    DomainSchema,
    SchemaLoader,
    detect_schema,
    get_schema_loader,
    reset_schema_loader
)


class TestUniversalFramework:
    """Test UniversalFramework dataclass."""

    def test_framework_creation(self):
        """Test basic framework creation."""
        framework = UniversalFramework(
            framework="Test framework content",
            domains={
                "test": DomainExpertise(
                    domain="test",
                    hints=["test"],
                    expertise="Test expertise"
                )
            },
            version="1.0"
        )

        assert framework.version == "1.0"
        assert "Test framework" in framework.get_framework()
        assert framework.get_domain_expertise("test") == "Test expertise"

    def test_framework_minimal(self):
        """Test framework with minimal fields."""
        framework = UniversalFramework()

        assert framework.framework == ""
        assert framework.domains == {}
        assert framework.get_framework() == ""
        assert framework.get_domain_expertise("nonexistent") is None

    def test_list_domains(self):
        """Test listing available domains."""
        framework = UniversalFramework(
            domains={
                "travel": DomainExpertise(domain="travel", expertise="..."),
                "code": DomainExpertise(domain="code", expertise="...")
            }
        )

        domains = framework.list_domains()
        assert "travel" in domains
        assert "code" in domains


class TestFrameworkLoader:
    """Test FrameworkLoader functionality."""

    @pytest.fixture(autouse=True)
    def reset_loader(self):
        """Reset singleton before each test."""
        reset_framework_loader()
        yield
        reset_framework_loader()

    def test_loader_singleton(self):
        """Test singleton pattern."""
        loader1 = get_framework_loader()
        loader2 = get_framework_loader()
        assert loader1 is loader2

    def test_load_universal_framework(self):
        """Test loading universal.yaml."""
        loader = get_framework_loader()

        framework = loader.get_problem_framework()
        assert len(framework) > 0
        assert "CONTEXT" in framework
        assert "GAP" in framework
        assert "CONSTRAINTS" in framework
        assert "DELIVERABLE" in framework

    def test_list_domains(self):
        """Test listing loaded domains."""
        loader = get_framework_loader()
        domains = loader.list_domains()

        assert isinstance(domains, list)
        assert len(domains) > 0
        # Should have these default domains
        assert "travel_planning" in domains
        assert "software_development" in domains

    def test_get_domain_expertise(self):
        """Test getting domain expertise."""
        loader = get_framework_loader()

        travel = loader.get_domain_expertise("travel_planning")
        assert travel is not None
        assert "預算" in travel  # Budget in Chinese

        nonexistent = loader.get_domain_expertise("nonexistent_domain")
        assert nonexistent is None


class TestConvenienceFunctions:
    """Test module-level convenience functions."""

    @pytest.fixture(autouse=True)
    def reset_loader(self):
        """Reset singleton before each test."""
        reset_framework_loader()
        yield
        reset_framework_loader()

    def test_get_problem_framework(self):
        """Test get_problem_framework function."""
        framework = get_problem_framework()

        assert len(framework) > 0
        assert "CONTEXT" in framework
        assert "GAP" in framework

    def test_get_domain_expertise(self):
        """Test get_domain_expertise function."""
        expertise = get_domain_expertise("software_development")

        assert expertise is not None
        assert "程式碼" in expertise or "code" in expertise.lower()


class TestBackwardCompatibility:
    """Test backward compatibility layer."""

    @pytest.fixture(autouse=True)
    def reset_loader(self):
        """Reset singleton before each test."""
        reset_schema_loader()
        yield
        reset_schema_loader()

    def test_schema_loader_still_works(self):
        """Test that SchemaLoader still works."""
        loader = get_schema_loader()

        # Should always return a schema (no keyword matching)
        schema = loader.match("any query")
        assert schema is not None
        assert schema.domain == "universal"

    def test_detect_schema_returns_universal(self):
        """Test that detect_schema returns universal framework."""
        # No matter what query, should return universal
        schema1 = detect_schema("規劃旅遊")
        schema2 = detect_schema("寫程式")
        schema3 = detect_schema("random query")

        assert schema1 is not None
        assert schema2 is not None
        assert schema3 is not None

        # All return universal framework
        assert "CONTEXT" in schema1.get_guidance()
        assert "GAP" in schema2.get_guidance()

    def test_domain_schema_get_guidance(self):
        """Test DomainSchema.get_guidance() returns framework."""
        schema = DomainSchema(domain="universal", detect=[])

        guidance = schema.get_guidance()
        assert "CONTEXT" in guidance
        assert "GAP" in guidance
        assert "CONSTRAINTS" in guidance
        assert "DELIVERABLE" in guidance

    def test_get_okr_prompt_alias(self):
        """Test that get_okr_prompt is alias for get_guidance."""
        schema = DomainSchema(domain="universal", detect=[])

        assert schema.get_okr_prompt() == schema.get_guidance()


class TestRouting:
    """Test routing configuration."""

    @pytest.fixture(autouse=True)
    def reset_loader(self):
        """Reset singleton before each test."""
        reset_framework_loader()
        yield
        reset_framework_loader()

    def test_routing_prompt_generated(self):
        """Test that routing prompt is generated with available domains."""
        from core.schema import get_routing_prompt

        routing_prompt = get_routing_prompt()

        # Should include available domains
        assert "Available Domains" in routing_prompt
        assert "travel_planning" in routing_prompt
        assert "software_development" in routing_prompt

    def test_routing_prompt_includes_hints(self):
        """Test that routing prompt includes domain hints."""
        from core.schema import get_routing_prompt

        routing_prompt = get_routing_prompt()

        # Should include hints from domain files
        assert "旅遊" in routing_prompt or "travel" in routing_prompt
        assert "coding" in routing_prompt or "寫程式" in routing_prompt

    def test_routing_strategy(self):
        """Test that routing strategy is configured."""
        loader = get_framework_loader()

        assert loader.framework.routing.strategy == "llm_decision"


class TestFrameworkContent:
    """Test the actual content of the framework."""

    @pytest.fixture(autouse=True)
    def reset_loader(self):
        """Reset singleton before each test."""
        reset_framework_loader()
        yield
        reset_framework_loader()

    def test_framework_has_four_elements(self):
        """Test framework contains all four elements."""
        framework = get_problem_framework()

        # Must have all four elements
        assert "CONTEXT" in framework
        assert "GAP" in framework
        assert "CONSTRAINTS" in framework
        assert "DELIVERABLE" in framework

    def test_framework_has_analysis_process(self):
        """Test framework contains analysis process."""
        framework = get_problem_framework()

        # Should describe the process
        assert "Extract" in framework or "extract" in framework
        assert "KNOWN" in framework or "UNKNOWN" in framework

    def test_domain_expertise_is_optional(self):
        """Test that domain expertise is truly optional."""
        # Framework should work without any domain expertise
        framework = get_problem_framework()
        assert len(framework) > 0

        # Getting nonexistent domain should return None, not crash
        result = get_domain_expertise("definitely_not_a_domain")
        assert result is None

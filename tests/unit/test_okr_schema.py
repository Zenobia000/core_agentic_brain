#!/usr/bin/env python3
"""
OKR Schema System Tests

Tests for the OKR-based domain schema system:
- Schema detection by keywords
- OKR prompt generation
- Key Results structure
- Constraints validation
"""

import pytest
from core.schema import (
    DomainSchema,
    SchemaLoader,
    detect_schema,
    get_schema_loader,
    reset_schema_loader
)


class TestDomainSchema:
    """Test DomainSchema dataclass functionality."""

    def test_schema_creation(self):
        """Test basic schema creation."""
        schema = DomainSchema(
            domain="test",
            detect=["test", "testing"],
            objective="Test objective",
            key_results={
                "kr1": {
                    "description": "First KR",
                    "checklist": ["Item 1", "Item 2"]
                }
            },
            constraints=["No errors"],
            success_criteria="All tests pass"
        )

        assert schema.domain == "test"
        assert "test" in schema.detect
        assert schema.objective == "Test objective"
        assert "kr1" in schema.key_results
        assert len(schema.constraints) == 1

    def test_matches_keyword(self):
        """Test keyword matching."""
        schema = DomainSchema(
            domain="travel",
            detect=["旅遊", "travel", "trip"]
        )

        assert schema.matches("規劃旅遊行程")
        assert schema.matches("Plan a travel itinerary")
        assert schema.matches("My trip to Japan")
        assert not schema.matches("Write some code")

    def test_matches_case_insensitive(self):
        """Test case-insensitive matching."""
        schema = DomainSchema(
            domain="code",
            detect=["coding", "FUNCTION"]
        )

        assert schema.matches("coding task")
        assert schema.matches("CODING task")
        assert schema.matches("create a function")
        assert schema.matches("CREATE A FUNCTION")

    def test_get_okr_prompt_complete(self):
        """Test OKR prompt generation with all fields."""
        schema = DomainSchema(
            domain="test",
            detect=["test"],
            objective="Complete the test",
            key_results={
                "setup": {
                    "description": "Setup phase",
                    "checklist": ["Install deps", "Configure env"]
                },
                "execution": {
                    "description": "Run tests",
                    "checklist": ["Unit tests", "Integration tests"]
                }
            },
            constraints=["No flaky tests", "Coverage > 80%"],
            success_criteria="All tests green"
        )

        okr = schema.get_okr_prompt()

        # Check structure
        assert "## OBJECTIVE" in okr
        assert "Complete the test" in okr
        assert "## KEY RESULTS" in okr
        assert "Setup" in okr
        assert "Execution" in okr
        assert "- [ ] Install deps" in okr
        assert "- [ ] Unit tests" in okr
        assert "## CONSTRAINTS" in okr
        assert "No flaky tests" in okr
        assert "## SUCCESS CRITERIA" in okr
        assert "All tests green" in okr

    def test_get_okr_prompt_minimal(self):
        """Test OKR prompt with minimal fields."""
        schema = DomainSchema(
            domain="minimal",
            detect=["min"]
        )

        okr = schema.get_okr_prompt()
        # Should not crash, may return empty or minimal string
        assert isinstance(okr, str)


class TestSchemaLoader:
    """Test SchemaLoader functionality."""

    @pytest.fixture(autouse=True)
    def reset_loader(self):
        """Reset singleton before each test."""
        reset_schema_loader()
        yield
        reset_schema_loader()

    def test_loader_singleton(self):
        """Test singleton pattern."""
        loader1 = get_schema_loader()
        loader2 = get_schema_loader()
        assert loader1 is loader2

    def test_list_domains(self):
        """Test listing loaded domains."""
        loader = get_schema_loader()
        domains = loader.list_domains()

        assert isinstance(domains, list)
        # Should have at least travel and code
        assert "travel" in domains
        assert "code" in domains

    def test_match_travel(self):
        """Test matching travel domain."""
        loader = get_schema_loader()

        # Chinese keywords
        schema = loader.match("規劃旅遊行程")
        assert schema is not None
        assert schema.domain == "travel"

        # English keywords
        schema = loader.match("Plan my vacation")
        assert schema is not None
        assert schema.domain == "travel"

    def test_match_code(self):
        """Test matching code domain."""
        loader = get_schema_loader()

        # Chinese keywords
        schema = loader.match("寫一個函數")
        assert schema is not None
        assert schema.domain == "code"

        # English keywords
        schema = loader.match("implement a function")
        assert schema is not None
        assert schema.domain == "code"

    def test_match_none(self):
        """Test no match returns None."""
        loader = get_schema_loader()

        schema = loader.match("random unrelated query")
        assert schema is None


class TestDetectSchema:
    """Test detect_schema convenience function."""

    @pytest.fixture(autouse=True)
    def reset_loader(self):
        """Reset singleton before each test."""
        reset_schema_loader()
        yield
        reset_schema_loader()

    def test_detect_travel(self):
        """Test detecting travel schema."""
        schema = detect_schema("規劃京都旅行")
        assert schema is not None
        assert schema.domain == "travel"
        assert "旅" in "".join(schema.detect)

    def test_detect_code(self):
        """Test detecting code schema."""
        schema = detect_schema("寫程式解決問題")
        assert schema is not None
        assert schema.domain == "code"

    def test_detect_with_okr(self):
        """Test that detected schema has valid OKR."""
        schema = detect_schema("規劃旅遊")
        assert schema is not None

        okr = schema.get_okr_prompt()
        assert "OBJECTIVE" in okr
        assert "KEY RESULTS" in okr

    def test_okr_has_checklist(self):
        """Test that OKR contains checklist items."""
        schema = detect_schema("travel planning")
        assert schema is not None

        okr = schema.get_okr_prompt()
        # Should have checkbox format
        assert "- [ ]" in okr


class TestOKRIntegration:
    """Integration tests for OKR flow."""

    @pytest.fixture(autouse=True)
    def reset_loader(self):
        """Reset singleton before each test."""
        reset_schema_loader()
        yield
        reset_schema_loader()

    def test_travel_okr_structure(self):
        """Test travel OKR has required sections."""
        schema = detect_schema("旅遊規劃")
        assert schema is not None

        okr = schema.get_okr_prompt()

        # Must have these sections for travel
        assert "prerequisites" in okr.lower() or "Prerequisites" in okr
        assert "budget" in okr.lower()
        assert "itinerary" in okr.lower()

    def test_code_okr_structure(self):
        """Test code OKR has required sections."""
        schema = detect_schema("寫程式")
        assert schema is not None

        okr = schema.get_okr_prompt()

        # Must have these sections for code
        assert "implementation" in okr.lower() or "Implementation" in okr
        assert "verification" in okr.lower() or "Verification" in okr

    def test_constraints_in_okr(self):
        """Test that constraints are included in OKR."""
        schema = detect_schema("travel")
        assert schema is not None
        assert len(schema.constraints) > 0

        okr = schema.get_okr_prompt()
        assert "CONSTRAINTS" in okr

        # At least one constraint should be present
        for constraint in schema.constraints:
            if constraint in okr:
                return  # Found at least one
        pytest.fail("No constraints found in OKR prompt")

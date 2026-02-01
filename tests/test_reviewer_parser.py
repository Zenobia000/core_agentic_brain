"""Unit tests for Reviewer parser."""

import pytest
from unittest.mock import MagicMock
from agents.reviewer import ReviewerAgent


class TestReviewerParser:
    """Test the _parse_review method."""

    @pytest.fixture
    def reviewer(self):
        """Create a reviewer agent for testing with mock LLM."""
        mock_llm = MagicMock()
        return ReviewerAgent(llm_provider=mock_llm)

    def test_parse_okr_format_approved(self, reviewer):
        """Test parsing OKR JSON format with APPROVED verdict."""
        review = '''
        Based on my review:
        {
            "key_results_status": {
                "itinerary": {
                    "day_by_day_plan": "PASS: Detailed 4-day plan provided",
                    "timing": "PASS: Morning/afternoon/evening specified"
                }
            },
            "constraints_violated": [],
            "verdict": "APPROVED",
            "revision_instructions": "",
            "summary": "All requirements met"
        }
        '''
        findings = reviewer._parse_review(review)

        assert findings["verdict"] == "APPROVED"
        assert findings["quality_score"] == 10
        assert findings["hard_constraints_passed"] is True
        assert len(findings["failed_constraints"]) == 0

    def test_parse_okr_format_revision_needed(self, reviewer):
        """Test parsing OKR JSON format with REVISION_NEEDED verdict."""
        review = '''
        {
            "key_results_status": {
                "budget": {
                    "breakdown": "FAIL: No specific numbers provided"
                }
            },
            "constraints_violated": [],
            "verdict": "REVISION_NEEDED",
            "revision_instructions": "Please provide specific budget breakdown with numbers",
            "summary": "Budget details missing"
        }
        '''
        findings = reviewer._parse_review(review)

        assert findings["verdict"] == "REVISION_NEEDED"
        assert findings["quality_score"] == 5
        assert findings["revision_instructions"] == "Please provide specific budget breakdown with numbers"
        assert len(findings["issues"]) == 1
        assert "FAIL" in findings["issues"][0]["description"]

    def test_parse_okr_format_with_constraints_violated(self, reviewer):
        """Test parsing when constraints are violated."""
        review = '''
        {
            "constraints_violated": ["Budget exceeded", "Missing accommodation"],
            "verdict": "REJECTED",
            "summary": "Critical constraints violated"
        }
        '''
        findings = reviewer._parse_review(review)

        assert findings["verdict"] == "REJECTED"
        assert findings["hard_constraints_passed"] is False
        assert len(findings["failed_constraints"]) == 2

    def test_parse_legacy_format(self, reviewer):
        """Test parsing legacy JSON format with hard_constraints_passed."""
        review = '''
        {
            "hard_constraints_passed": true,
            "verdict": "APPROVED",
            "quality_score": 8,
            "summary": "Good quality"
        }
        '''
        findings = reviewer._parse_review(review)

        assert findings["verdict"] == "APPROVED"
        assert findings["quality_score"] == 8
        assert findings["hard_constraints_passed"] is True

    def test_parse_text_fallback_approved(self, reviewer):
        """Test fallback text parsing when JSON fails."""
        review = '''
        Review complete.

        The result looks good.

        Verdict: APPROVED
        '''
        findings = reviewer._parse_review(review)

        assert findings["verdict"] == "APPROVED"
        assert findings["quality_score"] == 10

    def test_parse_text_fallback_revision_needed(self, reviewer):
        """Test fallback text parsing for REVISION_NEEDED."""
        review = '''
        Some issues found.

        REVISION_NEEDED - please fix the budget section.
        '''
        findings = reviewer._parse_review(review)

        assert findings["verdict"] == "REVISION_NEEDED"
        assert findings["quality_score"] == 5

    def test_needs_revision_approved(self, reviewer):
        """Test _needs_revision returns False for approved."""
        findings = {
            "verdict": "APPROVED",
            "quality_score": 10,
            "hard_constraints_passed": True,
            "issues": []
        }
        assert reviewer._needs_revision(findings) is False

    def test_needs_revision_low_score(self, reviewer):
        """Test _needs_revision returns True for low score."""
        findings = {
            "verdict": "UNKNOWN",
            "quality_score": 3,
            "hard_constraints_passed": True,
            "issues": []
        }
        assert reviewer._needs_revision(findings) is True

    def test_needs_revision_constraints_failed(self, reviewer):
        """Test _needs_revision returns True when constraints failed."""
        findings = {
            "verdict": "APPROVED",
            "quality_score": 10,
            "hard_constraints_passed": False,
            "issues": []
        }
        assert reviewer._needs_revision(findings) is True

    def test_parse_guidance_format_approved(self, reviewer):
        """Test parsing guidance-based JSON format with APPROVED verdict."""
        review = '''
        {
            "criteria_check": {
                "Complete budget breakdown": "PASS: Detailed budget provided",
                "Day-by-day itinerary": "PASS: All days have activities"
            },
            "prohibitions_violated": [],
            "verdict": "APPROVED",
            "revision_instructions": "",
            "summary": "All delivery criteria met"
        }
        '''
        findings = reviewer._parse_review(review)

        assert findings["verdict"] == "APPROVED"
        assert findings["quality_score"] == 10
        assert findings["hard_constraints_passed"] is True
        assert len(findings["issues"]) == 0

    def test_parse_guidance_format_revision_needed(self, reviewer):
        """Test parsing guidance-based format with REVISION_NEEDED verdict."""
        review = '''
        {
            "criteria_check": {
                "Complete budget breakdown": "FAIL: Only total provided, no breakdown",
                "Day-by-day itinerary": "PASS: All days covered"
            },
            "prohibitions_violated": [],
            "verdict": "REVISION_NEEDED",
            "revision_instructions": "Add detailed budget breakdown",
            "summary": "Budget details incomplete"
        }
        '''
        findings = reviewer._parse_review(review)

        assert findings["verdict"] == "REVISION_NEEDED"
        assert findings["quality_score"] == 5
        assert len(findings["issues"]) == 1
        assert "FAIL" in findings["issues"][0]["description"]

    def test_parse_guidance_format_with_prohibitions(self, reviewer):
        """Test parsing when prohibitions are violated."""
        review = '''
        {
            "criteria_check": {},
            "prohibitions_violated": ["Assumed travel dates without asking"],
            "verdict": "REJECTED",
            "summary": "Violated prohibition against assumptions"
        }
        '''
        findings = reviewer._parse_review(review)

        assert findings["verdict"] == "REJECTED"
        assert findings["hard_constraints_passed"] is False
        assert len(findings["failed_constraints"]) == 1

    def test_parse_universal_format_approved(self, reviewer):
        """Test parsing universal element_check format with APPROVED."""
        review = '''
        {
            "element_check": {
                "context": "PASS: User context understood",
                "gap": "PASS: Problem solved",
                "constraints": "PASS: All constraints met",
                "deliverable": "PASS: Output complete"
            },
            "verdict": "APPROVED",
            "summary": "All elements satisfied"
        }
        '''
        findings = reviewer._parse_review(review)

        assert findings["verdict"] == "APPROVED"
        assert findings["quality_score"] == 10
        assert findings["hard_constraints_passed"] is True
        assert len(findings["issues"]) == 0

    def test_parse_universal_format_revision_needed(self, reviewer):
        """Test parsing universal format with REVISION_NEEDED."""
        review = '''
        {
            "element_check": {
                "context": "PASS: Understood",
                "gap": "FAIL: Gap not fully closed - missing budget details",
                "constraints": "PASS: Within budget",
                "deliverable": "FAIL: Missing day-by-day itinerary"
            },
            "verdict": "REVISION_NEEDED",
            "revision_instructions": "Add budget breakdown and daily schedule",
            "summary": "Incomplete deliverable"
        }
        '''
        findings = reviewer._parse_review(review)

        assert findings["verdict"] == "REVISION_NEEDED"
        assert findings["quality_score"] == 5
        assert len(findings["issues"]) == 2  # gap and deliverable failed

    def test_parse_universal_format_constraints_violated(self, reviewer):
        """Test parsing universal format with constraints violation."""
        review = '''
        {
            "element_check": {
                "context": "PASS",
                "gap": "PASS",
                "constraints": "FAIL: Budget exceeded by 30%",
                "deliverable": "PASS"
            },
            "verdict": "REJECTED",
            "summary": "Budget constraint violated"
        }
        '''
        findings = reviewer._parse_review(review)

        assert findings["verdict"] == "REJECTED"
        assert findings["hard_constraints_passed"] is False
        assert len(findings["failed_constraints"]) == 1

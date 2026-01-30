"""Review agent for quality assurance."""

import re
import json
from typing import Dict, List, Any
from agents.base import BaseAgent
from core.types import TaskContext, ExecutionResult
from core.logger import log
from core.prompt_loader import get_prompt_loader


class ReviewerAgent(BaseAgent):
    """Agent responsible for reviewing and validating execution results.

    所有 prompt 從 YAML 載入，Agent 只負責執行邏輯。
    """

    def __init__(self):
        """Initialize reviewer agent."""
        super().__init__("Reviewer")
        self._prompt_loader = get_prompt_loader()

    def get_system_prompt(self) -> str:
        """Get review-specific system prompt from YAML."""
        return self._prompt_loader.get("reviewer.system")

    async def execute(self, context: TaskContext) -> ExecutionResult:
        """Review the execution results."""
        log.agent("reviewer", "Reviewing execution results")

        try:
            # Get previous execution result to review
            previous_result = context.metadata.get("previous_result", "")
            execution_result = context.metadata.get("execution_result")
            if execution_result:
                previous_result = execution_result.response if hasattr(execution_result, 'response') else str(execution_result)

            original_task = context.prompt

            # Build review prompt from YAML template
            review_prompt = self._build_review_prompt(original_task, previous_result)

            # Get review from LLM
            review = await self._call_llm(review_prompt, context)

            # Parse review findings
            findings = self._parse_review(review)

            # Enforce hard constraints
            findings = self._check_hard_constraints(findings)

            # Determine if revision is needed
            needs_revision = self._needs_revision(findings)

            verdict = findings.get('verdict', 'UNKNOWN')
            score = findings.get('quality_score', 0)
            if verdict == "APPROVED":
                log.agent_done("reviewer", f"Verdict: {verdict} (score: {score})")
            else:
                log.agent("reviewer", f"Verdict: {verdict} (score: {score})")
                if needs_revision:
                    log.warning(f"Revision needed: {len(findings.get('issues', []))} issues")

            return ExecutionResult(
                success=True,
                response=review,
                metadata={
                    "agent": "reviewer",
                    "needs_revision": needs_revision,
                    "needs_improvement": needs_revision,  # Backward compatibility
                    "findings": findings,
                    "quality_score": findings.get("quality_score", 0),
                    "verdict": findings.get("verdict", "UNKNOWN")
                }
            )

        except Exception as e:
            log.failure(f"Review failed: {str(e)}")
            return ExecutionResult(
                success=False,
                response="",
                error=f"Review failed: {str(e)}"
            )

    def _build_review_prompt(self, task: str, result: str) -> str:
        """Build review prompt from YAML template.

        純粹的模板填充，無硬編碼 prompt。
        """
        review_template = self._prompt_loader.get("reviewer.review")
        return review_template.format(task=task, result=result)

    def _parse_review(self, review: str) -> Dict[str, Any]:
        """Parse review text into structured findings."""
        findings = {
            "issues": [],
            "recommendations": [],
            "quality_score": 0,
            "verdict": "UNKNOWN",
            "hard_constraints_passed": True,
            "failed_constraints": []
        }

        # Try JSON first (new format with hard constraints)
        json_match = re.search(r'\{[^{}]*"hard_constraints_passed"[^{}]*\}', review, re.DOTALL)
        if json_match:
            try:
                parsed = json.loads(json_match.group())
                return {
                    "issues": [],
                    "recommendations": [],
                    "quality_score": parsed.get("quality_score", 0),
                    "verdict": parsed.get("verdict", "UNKNOWN"),
                    "hard_constraints_passed": parsed.get("hard_constraints_passed", True),
                    "failed_constraints": parsed.get("failed_constraints", []),
                    "summary": parsed.get("summary", "")
                }
            except json.JSONDecodeError:
                pass

        # Fallback to original text parsing
        lines = review.split('\n')
        current_section = None

        for line in lines:
            line = line.strip()

            # Identify sections
            if "Issues Found" in line or "Problems" in line:
                current_section = "issues"
            elif "Recommendations" in line or "Improvements" in line:
                current_section = "recommendations"
            elif "Quality" in line and any(char.isdigit() for char in line):
                # Extract quality score
                numbers = re.findall(r'\d+', line)
                if numbers:
                    findings["quality_score"] = int(numbers[0])
            elif "APPROVED" in line:
                findings["verdict"] = "APPROVED"
            elif "REVISION_NEEDED" in line:
                findings["verdict"] = "REVISION_NEEDED"
            elif "REJECTED" in line:
                findings["verdict"] = "REJECTED"
            elif current_section and line and line[0] in '-•*':
                # Add to current section
                if current_section == "issues":
                    findings["issues"].append(self._parse_issue(line))
                elif current_section == "recommendations":
                    findings["recommendations"].append(line[1:].strip())

        return findings

    def _parse_issue(self, issue_line: str) -> Dict[str, str]:
        """Parse an issue line into structured format."""
        # Remove bullet point
        issue_text = issue_line.lstrip('-•* ').strip()

        # Try to extract severity
        severity = "Medium"  # Default
        if "High" in issue_text or "Critical" in issue_text:
            severity = "High"
        elif "Low" in issue_text or "Minor" in issue_text:
            severity = "Low"

        return {
            "description": issue_text,
            "severity": severity
        }

    def _check_hard_constraints(self, findings: Dict[str, Any]) -> Dict[str, Any]:
        """Force REJECTED if hard constraints failed."""
        if not findings.get("hard_constraints_passed", True):
            log.warning(f"Hard constraints failed: {findings.get('failed_constraints', [])}")
            findings["verdict"] = "REJECTED"
            findings["needs_revision"] = True
        return findings

    def _needs_revision(self, findings: Dict[str, Any]) -> bool:
        """Determine if revision is needed based on findings."""
        # Check hard constraints first
        if not findings.get("hard_constraints_passed", True):
            return True

        # Check verdict
        if findings.get("verdict") in ["REVISION_NEEDED", "REJECTED"]:
            return True

        # Check for high severity issues
        high_severity_issues = [
            issue for issue in findings.get("issues", [])
            if issue.get("severity") == "High"
        ]
        if high_severity_issues:
            return True

        # Check quality score
        if findings.get("quality_score", 10) < 6:
            return True

        return False

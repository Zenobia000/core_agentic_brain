"""Review agent for quality assurance."""

from typing import Dict, List, Any
from agents.base import BaseAgent
from core.types import TaskContext, ExecutionResult
from core.simple_logger import log
from core.prompt_loader import get_prompt_loader


class ReviewerAgent(BaseAgent):
    """Agent responsible for reviewing and validating execution results."""

    def __init__(self):
        """Initialize reviewer agent."""
        super().__init__("Reviewer")

    def get_system_prompt(self) -> str:
        """Get review-specific system prompt from YAML template."""
        prompt_loader = get_prompt_loader()
        return prompt_loader.get("reviewer.system")

    async def execute(self, context: TaskContext) -> ExecutionResult:
        """Review the execution results."""
        log('info', summary="Reviewing execution results")

        try:
            # Get previous execution result to review
            previous_result = context.metadata.get("previous_result", "")
            original_task = context.prompt

            # Create review prompt
            review_prompt = self._create_review_prompt(original_task, previous_result)

            # Get review from LLM
            review = await self._call_llm(review_prompt, context)

            # Parse review findings
            findings = self._parse_review(review)

            # Determine if revision is needed
            needs_revision = self._needs_revision(findings)

            log('info', summary="Review complete",
                       needs_revision=needs_revision,
                       issues_found=len(findings.get("issues", [])))

            return ExecutionResult(
                success=True,
                response=review,
                metadata={
                    "agent": "reviewer",
                    "needs_revision": needs_revision,
                    "findings": findings,
                    "quality_score": findings.get("quality_score", 0)
                }
            )

        except Exception as e:
            log('error', summary="Review failed", error=str(e))
            return ExecutionResult(
                success=False,
                response="",
                error=f"Review failed: {str(e)}"
            )

    def _create_review_prompt(self, task: str, result: str) -> str:
        """Create a prompt for reviewing execution results."""
        return f"""Please review the following task execution:

Original Task:
{task}

Execution Result:
{result}

Please provide a comprehensive review including:

1. **Correctness Assessment**
   - Is the solution logically correct?
   - Does it fully address the requirements?
   - Are there any errors or mistakes?

2. **Completeness Check**
   - Are all aspects of the task addressed?
   - Is anything missing or incomplete?
   - Are edge cases considered?

3. **Quality Evaluation**
   - Rate the overall quality (1-10)
   - Is the solution optimal?
   - Are there better approaches?

4. **Issues Found**
   - List any specific problems
   - Severity of each issue (High/Medium/Low)

5. **Recommendations**
   - Suggested improvements
   - Alternative approaches
   - Performance optimizations

6. **Final Verdict**
   - APPROVED: Ready for use
   - REVISION_NEEDED: Requires changes
   - REJECTED: Major issues found"""

    def _parse_review(self, review: str) -> Dict[str, Any]:
        """Parse review text into structured findings."""
        findings = {
            "issues": [],
            "recommendations": [],
            "quality_score": 0,
            "verdict": "UNKNOWN"
        }

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
                import re
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

    def _needs_revision(self, findings: Dict[str, Any]) -> bool:
        """Determine if revision is needed based on findings."""
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
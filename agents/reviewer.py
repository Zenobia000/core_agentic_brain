"""Review agent for quality assurance."""

import re
import json
from typing import Dict, List, Any, Optional, TYPE_CHECKING
from agents.base import BaseAgent
from core.types import TaskContext, ExecutionResult
from core.logger import log
from core.prompt_loader import get_prompt_loader

if TYPE_CHECKING:
    from core.llm import LLMProvider
    from core.kernel import Kernel


class ReviewerAgent(BaseAgent):
    """Agent responsible for reviewing and validating execution results.

    所有 prompt 從 YAML 載入，Agent 只負責執行邏輯。
    """

    def __init__(
        self,
        llm_provider: Optional["LLMProvider"] = None,
        kernel: Optional["Kernel"] = None
    ):
        """Initialize reviewer agent."""
        super().__init__("Reviewer", llm_provider=llm_provider, kernel=kernel)
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

            # Build review prompt from YAML template (OKR-first)
            review_prompt = self._build_review_prompt(original_task, previous_result, context)

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

    def _build_review_prompt(self, task: str, result: str, context: TaskContext = None) -> str:
        """Build review prompt from YAML template.

        OKR-first: 優先使用 OKR prompt 進行 checklist 驗證。
        """
        # Check if OKR is available
        okr_prompt = None
        if context and context.metadata:
            okr_prompt = context.metadata.get("okr_prompt")

        if okr_prompt:
            # Use OKR-based review prompt
            log.debug("Using OKR-based review prompt")
            review_template = self._prompt_loader.get("reviewer.review_okr")
            return review_template.format(
                okr_prompt=okr_prompt,
                result=result
            )

        # Fallback: no OKR available
        review_template = self._prompt_loader.get("reviewer.review")
        return review_template.format(task=task, result=result)

    def _parse_review(self, review: str) -> Dict[str, Any]:
        """Parse review text into structured findings.

        Supports multiple JSON formats:
        1. Universal format: {verdict, element_check, ...}
        2. Guidance format: {verdict, criteria_check, prohibitions_violated, ...}
        3. OKR format: {verdict, constraints_violated, key_results_status, ...}
        4. Legacy format: {verdict, hard_constraints_passed, quality_score, ...}
        """
        # Default findings - verdict-based scoring
        findings = {
            "issues": [],
            "recommendations": [],
            "quality_score": 0,
            "verdict": "UNKNOWN",
            "hard_constraints_passed": True,
            "failed_constraints": [],
            "revision_instructions": ""
        }

        # Try to extract JSON from response (find the outermost {})
        json_match = re.search(r'\{[\s\S]*\}', review)
        if json_match:
            try:
                # Clean common LLM JSON errors before parsing
                json_str = self._clean_json(json_match.group())
                parsed = json.loads(json_str)

                # Extract verdict (all formats use this)
                verdict = parsed.get("verdict", "UNKNOWN")
                findings["verdict"] = verdict

                # Handle universal format (element_check)
                if "element_check" in parsed:
                    element_check = parsed.get("element_check", {})
                    # Check constraints element specifically
                    constraints_status = element_check.get("constraints", "")
                    if isinstance(constraints_status, str) and "FAIL" in constraints_status.upper():
                        findings["hard_constraints_passed"] = False
                        findings["failed_constraints"].append(constraints_status)

                    # Extract issues from failed elements
                    for element, status in element_check.items():
                        if isinstance(status, str) and "FAIL" in status.upper():
                            findings["issues"].append({
                                "description": f"[{element}] {status}",
                                "severity": "High" if element == "constraints" else "Medium"
                            })

                # Handle guidance format (prohibitions_violated)
                elif "prohibitions_violated" in parsed:
                    prohibitions = parsed.get("prohibitions_violated", [])
                    findings["hard_constraints_passed"] = len(prohibitions) == 0
                    findings["failed_constraints"] = prohibitions

                # Handle OKR format (constraints_violated)
                elif "constraints_violated" in parsed:
                    constraints = parsed.get("constraints_violated", [])
                    findings["hard_constraints_passed"] = len(constraints) == 0
                    findings["failed_constraints"] = constraints

                # Handle legacy format (hard_constraints_passed)
                elif "hard_constraints_passed" in parsed:
                    findings["hard_constraints_passed"] = parsed.get("hard_constraints_passed", True)
                    findings["failed_constraints"] = parsed.get("failed_constraints", [])

                # Extract revision instructions
                findings["revision_instructions"] = parsed.get("revision_instructions", "")
                findings["summary"] = parsed.get("summary", "")

                # Extract or derive quality score
                if "quality_score" in parsed:
                    findings["quality_score"] = parsed.get("quality_score", 0)
                else:
                    # Derive score from verdict
                    score_map = {"APPROVED": 10, "REVISION_NEEDED": 5, "REJECTED": 0}
                    findings["quality_score"] = score_map.get(verdict, 0)

                # Extract issues from criteria_check (guidance format)
                if "criteria_check" in parsed:
                    for item, status in parsed.get("criteria_check", {}).items():
                        if isinstance(status, str) and "FAIL" in status.upper():
                            findings["issues"].append({
                                "description": f"{item}: {status}",
                                "severity": "High"
                            })

                # Extract issues from key_results_status (OKR format)
                elif "key_results_status" in parsed:
                    for kr_name, items in parsed.get("key_results_status", {}).items():
                        if isinstance(items, dict):
                            for item, status in items.items():
                                if isinstance(status, str) and status.startswith("FAIL"):
                                    findings["issues"].append({
                                        "description": f"[{kr_name}] {item}: {status}",
                                        "severity": "High"
                                    })

                log.debug(f"Parsed review JSON: verdict={verdict}, score={findings['quality_score']}")
                return findings

            except json.JSONDecodeError as e:
                log.warning(f"Failed to parse review JSON: {e}")

        # Fallback to text parsing
        lines = review.split('\n')
        current_section = None

        for line in lines:
            line = line.strip()

            # Detect verdict keywords anywhere in text
            if "APPROVED" in line.upper():
                findings["verdict"] = "APPROVED"
                findings["quality_score"] = 10
            elif "REVISION_NEEDED" in line.upper() or "REVISION NEEDED" in line.upper():
                findings["verdict"] = "REVISION_NEEDED"
                findings["quality_score"] = 5
            elif "REJECTED" in line.upper():
                findings["verdict"] = "REJECTED"
                findings["quality_score"] = 0

            # Identify sections
            if "Issues Found" in line or "Problems" in line or "FAIL" in line:
                current_section = "issues"
            elif "Recommendations" in line or "Improvements" in line:
                current_section = "recommendations"
            elif "Quality" in line and any(char.isdigit() for char in line):
                numbers = re.findall(r'\d+', line)
                if numbers:
                    findings["quality_score"] = int(numbers[0])
            elif current_section and line and line[0] in '-•*':
                if current_section == "issues":
                    findings["issues"].append(self._parse_issue(line))
                elif current_section == "recommendations":
                    findings["recommendations"].append(line[1:].strip())

        return findings

    def _clean_json(self, json_str: str) -> str:
        """Clean common LLM JSON errors before parsing.

        Handles:
        - Trailing commas in objects and arrays
        - Single quotes (converts to double quotes)
        - Unescaped newlines in strings
        """
        # Remove trailing commas before } or ]
        # Pattern: comma followed by optional whitespace, then } or ]
        json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)

        return json_str

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

"""Planning agent for task decomposition."""

from typing import List, Dict, Any
from agents.base import BaseAgent
from core.types import TaskContext, ExecutionResult
from core.simple_logger import log
from core.prompt_loader import get_prompt_loader


class PlannerAgent(BaseAgent):
    """Agent responsible for planning and task decomposition."""

    def __init__(self):
        """Initialize planner agent."""
        super().__init__("Planner")

    def get_system_prompt(self) -> str:
        """Get planning-specific system prompt from YAML template."""
        prompt_loader = get_prompt_loader()
        return prompt_loader.get("planner.system")

    async def execute(self, context: TaskContext) -> ExecutionResult:
        """Execute planning for the given task."""
        log('info', summary="Planning task execution", prompt=context.prompt[:50])

        try:
            # Create planning prompt
            planning_prompt = self._create_planning_prompt(context)

            # Get plan from LLM
            plan = await self._call_llm(planning_prompt, context)

            # Parse plan into steps
            steps = self._parse_plan(plan)

            # Log plan details
            log('info', summary=f"Created plan with {len(steps)} steps")

            return ExecutionResult(
                success=True,
                response=plan,
                metadata={
                    "agent": "planner",
                    "steps_count": len(steps),
                    "steps": steps
                }
            )

        except Exception as e:
            log('error', summary="Planning failed", error=str(e))
            return ExecutionResult(
                success=False,
                response="",
                error=f"Planning failed: {str(e)}"
            )

    def _create_planning_prompt(self, context: TaskContext) -> str:
        """Create a prompt for planning."""
        prompt = f"""Please create a detailed plan for the following task:

Task: {context.prompt}

Available Tools: {', '.join(context.tools) if context.tools else 'Standard tools'}

Please provide:
1. A step-by-step plan with numbered steps
2. Dependencies between steps (if any)
3. Required tools or resources for each step
4. Estimated complexity for each step
5. Potential risks or considerations

Be specific and actionable in your planning."""
        return prompt

    def _parse_plan(self, plan: str) -> List[Dict[str, Any]]:
        """Parse plan text into structured steps."""
        steps = []
        lines = plan.split('\n')

        current_step = None
        step_number = 0

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check if line starts with a number (new step)
            if line and (line[0].isdigit() or line.startswith('-')):
                if current_step:
                    steps.append(current_step)

                step_number += 1
                current_step = {
                    "number": step_number,
                    "description": line,
                    "details": []
                }
            elif current_step:
                # Add as detail to current step
                current_step["details"].append(line)

        # Add last step if exists
        if current_step:
            steps.append(current_step)

        return steps
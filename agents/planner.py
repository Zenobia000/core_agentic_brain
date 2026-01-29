"""Planning agent for task decomposition."""

import json
from typing import List, Dict, Any
from agents.base import BaseAgent
from core.types import TaskContext, ExecutionResult
from core.logger import logger, contextualize
from core.prompt_loader import get_prompt_loader


class PlannerAgent(BaseAgent):
    """Agent responsible for planning and task decomposition.

    所有 prompt 從 YAML 載入，Agent 只負責執行邏輯。
    """

    def __init__(self):
        """Initialize planner agent."""
        super().__init__("Planner")
        self._prompt_loader = get_prompt_loader()

    def get_system_prompt(self) -> str:
        """Get planning-specific system prompt from YAML."""
        return self._prompt_loader.get("planner.system")

    async def execute(self, context: TaskContext) -> ExecutionResult:
        """Execute planning for the given task."""
        run_id = context.run_id or "unknown"

        with contextualize(run_id=run_id, agent="PlannerAgent"):
            prompt_preview = context.prompt[:50] + "..." if len(context.prompt) > 50 else context.prompt
            logger.info(f"Planning started for task: '{prompt_preview}'")

            try:
                # Build planning prompt from YAML template
                planning_prompt = self._build_planning_prompt(context)

                # Get plan from LLM
                plan = await self._call_llm(planning_prompt, context)

                # Parse plan into steps
                steps = self._parse_plan(plan)

                logger.debug(f"Plan created: {steps}")
                logger.info(f"Planning completed with {len(steps)} steps")

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
                logger.error(f"Planning failed: {str(e)}")
                return ExecutionResult(
                    success=False,
                    response="",
                    error=f"Planning failed: {str(e)}"
                )

    def _build_planning_prompt(self, context: TaskContext) -> str:
        """Build planning prompt from YAML template.

        純粹的模板填充，無硬編碼 prompt。
        """
        # Build System 2 context if available
        system2_context = ""
        if context.metadata and context.metadata.get("system_2_thought_process"):
            system2_template = self._prompt_loader.get("planner.system2_context_template")
            system2_context = system2_template.format(
                original_prompt=context.metadata.get('original_prompt', 'N/A'),
                thought_process=context.metadata.get('system_2_thought_process', ''),
                key_questions=json.dumps(
                    context.metadata.get('key_questions', []),
                    indent=2,
                    ensure_ascii=False
                )
            )

        # Get tools list
        tools = ', '.join(context.tools) if context.tools else 'Standard tools'

        # Load and fill planning template
        planning_template = self._prompt_loader.get("planner.planning")
        return planning_template.format(
            task=context.prompt,
            system2_context=system2_context,
            tools=tools
        )

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

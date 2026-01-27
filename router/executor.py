"""
Router executor for task routing and orchestration.
Executes tasks based on routing decisions.
"""

import asyncio
import time
from typing import Dict, List, Optional, Any
from core.types import RouterDecision, TaskResult, TaskComplexity
from core.tools import ToolManager


class RouterExecutor:
    """Execute tasks based on routing decisions"""

    def __init__(self, tool_manager: ToolManager, config: Optional[Dict] = None):
        self.tool_manager = tool_manager
        self.config = config or {}

    async def execute(
        self,
        decision: RouterDecision,
        task: str,
        context: Optional[Dict] = None
    ) -> TaskResult:
        """
        Execute task based on routing decision.

        Args:
            decision: Routing decision from analyzer
            task: Original task string
            context: Optional execution context

        Returns:
            TaskResult with execution outcome
        """
        start_time = time.time()

        try:
            if decision.strategy == "fast_path":
                result = await self._execute_fast_path(task, context)
            else:
                result = await self._execute_agent_path(
                    decision.agents, task, context
                )

            execution_time = time.time() - start_time

            return TaskResult(
                success=True,
                output=result,
                complexity=decision.complexity,
                execution_time=execution_time,
                agent_path=decision.agents if decision.strategy == "agent_path" else []
            )

        except Exception as e:
            execution_time = time.time() - start_time
            return TaskResult(
                success=False,
                output=None,
                complexity=decision.complexity,
                execution_time=execution_time,
                errors=[str(e)]
            )

    async def _execute_fast_path(
        self,
        task: str,
        context: Optional[Dict] = None
    ) -> Any:
        """Execute task directly using tools"""
        # Determine primary tool for task
        tool_name = self._select_primary_tool(task)

        if not self.tool_manager.get_tool(tool_name):
            raise ValueError(f"Tool '{tool_name}' not available")

        # Execute with simplified parameters
        return await self.tool_manager.execute(
            tool_name,
            task=task,
            context=context
        )

    async def _execute_agent_path(
        self,
        agents: List[str],
        task: str,
        context: Optional[Dict] = None
    ) -> Any:
        """Execute task using agent orchestration"""
        results = {}

        for agent_name in agents:
            # Simulate agent execution (placeholder for actual implementation)
            agent_result = await self._execute_agent(
                agent_name, task, context, results
            )
            results[agent_name] = agent_result

        return results

    async def _execute_agent(
        self,
        agent_name: str,
        task: str,
        context: Optional[Dict],
        previous_results: Dict
    ) -> Any:
        """Execute individual agent (placeholder)"""
        # This is a placeholder for actual agent execution
        # In full implementation, this would instantiate and run specific agents
        await asyncio.sleep(0.1)  # Simulate processing

        if agent_name == "planner":
            return {"plan": f"Plan for: {task}", "steps": ["step1", "step2"]}
        elif agent_name == "executor":
            return {"execution": f"Executed: {task}", "status": "success"}
        elif agent_name == "reviewer":
            return {"review": "Task completed successfully", "quality": "good"}
        else:
            return {"agent": agent_name, "result": "completed"}

    def _select_primary_tool(self, task: str) -> str:
        """Select primary tool based on task content"""
        task_lower = task.lower()

        if "python" in task_lower or "code" in task_lower:
            return "python"
        elif "file" in task_lower:
            return "files"
        else:
            # Default to python tool
            return "python"
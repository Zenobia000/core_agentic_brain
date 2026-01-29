"""Execution agent for carrying out tasks."""

import time
from typing import Any, Dict, List
from agents.base import BaseAgent
from core.types import TaskContext, ExecutionResult, ToolCall
from core.simple_logger import log
from core.prompt_loader import get_prompt_loader


class ExecutorAgent(BaseAgent):
    """Agent responsible for executing tasks and tool calls."""

    def __init__(self):
        """Initialize executor agent."""
        super().__init__("Executor")

    def get_system_prompt(self) -> str:
        """Get execution-specific system prompt from YAML template."""
        prompt_loader = get_prompt_loader()
        return prompt_loader.get("executor.system")

    async def execute(self, context: TaskContext) -> ExecutionResult:
        """Execute the given task."""
        log('info', summary="Executing task", prompt=context.prompt[:50])

        try:
            # Check if there's a plan to follow
            plan = context.metadata.get("plan")
            if plan:
                return await self._execute_with_plan(context, plan)
            else:
                return await self._execute_directly(context)

        except Exception as e:
            log('error', summary="Execution failed", error=str(e))
            return ExecutionResult(
                success=False,
                response="",
                error=f"Execution failed: {str(e)}"
            )

    async def _execute_directly(self, context: TaskContext) -> ExecutionResult:
        """Execute task directly without a plan."""
        start_time = time.time()

        # Create execution prompt
        exec_prompt = f"""Execute the following task:

Task: {context.prompt}

Available tools: {', '.join(context.tools) if context.tools else 'Standard tools'}

Provide a clear response and use tools as needed."""

        # Get response from LLM
        response = await self._call_llm(exec_prompt, context)

        # Extract and execute tool calls
        tool_calls = self._extract_tool_calls(response)
        tool_results = []

        if tool_calls:
            log('info', summary=f"Executing {len(tool_calls)} tool calls")
            tool_results = await self._execute_tool_calls(tool_calls)

        # Calculate execution time
        execution_time = (time.time() - start_time) * 1000

        return ExecutionResult(
            success=True,
            response=response,
            tool_calls=[
                ToolCall(
                    name=tc["name"],
                    parameters=tc["parameters"],
                    result=result.get("result") if result else None,
                    error=result.get("error") if result else None
                )
                for tc, result in zip(tool_calls, tool_results)
            ],
            metadata={
                "agent": "executor",
                "execution_time_ms": execution_time,
                "tool_count": len(tool_calls)
            }
        )

    async def _execute_with_plan(self, context: TaskContext, plan: Dict[str, Any]) -> ExecutionResult:
        """Execute task following a plan."""
        log('info', summary="Executing with plan", steps=len(plan.get("steps", [])))

        results = []
        overall_success = True

        for step in plan.get("steps", []):
            log('debug', summary=f"Executing step {step.get('number')}: {step.get('description')[:50]}")

            # Execute each step
            step_result = await self._execute_step(context, step)
            results.append(step_result)

            if not step_result["success"]:
                overall_success = False
                log('warning', summary=f"Step {step.get('number')} failed")
                break

        # Compile final response
        response = self._compile_results(results)

        return ExecutionResult(
            success=overall_success,
            response=response,
            metadata={
                "agent": "executor",
                "plan_steps": len(plan.get("steps", [])),
                "executed_steps": len(results),
                "with_plan": True
            }
        )

    async def _execute_step(self, context: TaskContext, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single step from the plan."""
        try:
            # Create step-specific prompt
            step_prompt = f"Execute step: {step.get('description')}\nDetails: {' '.join(step.get('details', []))}"

            # Execute
            response = await self._call_llm(step_prompt, context)

            # Check for tool calls
            tool_calls = self._extract_tool_calls(response)
            if tool_calls:
                await self._execute_tool_calls(tool_calls)

            return {
                "step": step.get("number"),
                "success": True,
                "response": response
            }

        except Exception as e:
            return {
                "step": step.get("number"),
                "success": False,
                "error": str(e)
            }

    async def _execute_tool_calls(self, tool_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute tool calls."""
        results = []

        for tool_call in tool_calls:
            start_time = time.time()
            try:
                log('debug', summary=f"Executing tool: {tool_call['name']}")

                # Get and execute tool
                tool = self.tool_manager.get_tool(tool_call["name"])
                if tool:
                    result = await tool.execute(**tool_call["parameters"])
                    duration = (time.time() - start_time) * 1000

                    results.append({
                        "success": True,
                        "result": result,
                        "duration_ms": duration
                    })
                else:
                    results.append({
                        "success": False,
                        "error": f"Tool {tool_call['name']} not found"
                    })

            except Exception as e:
                log('error', summary=f"Tool execution failed: {tool_call['name']}", error=str(e))
                results.append({
                    "success": False,
                    "error": str(e)
                })

        return results

    def _compile_results(self, results: List[Dict[str, Any]]) -> str:
        """Compile step results into final response."""
        response_parts = []

        for result in results:
            if result["success"]:
                response_parts.append(f"Step {result['step']}: ✓ {result.get('response', 'Completed')}")
            else:
                response_parts.append(f"Step {result['step']}: ✗ Failed - {result.get('error', 'Unknown error')}")

        return "\n".join(response_parts)
"""
Execution agent with ReAct loop - Think, Act, Observe pattern
Based on Linus: Simple tools that do one thing well
"""

import json
import time
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from collections import deque
from agents.base import BaseAgent
from core.types import (
    TaskContext, ExecutionResult, ToolCall, Message, MessageRole,
    ReactConfig, ToolCallSignature
)
from core.logger import logger, contextualize
from core.prompt_loader import get_prompt_loader
from core.llm import LLMProvider

if TYPE_CHECKING:
    from core.kernel import Kernel


class ExecutorAgent(BaseAgent):
    """Agent with internal ReAct loop for complex task execution.

    所有 prompt 從 YAML 載入，Agent 只負責執行邏輯。
    """

    def __init__(
        self,
        llm_provider: Optional[LLMProvider] = None,
        kernel: Optional["Kernel"] = None,
        react_config: Optional[ReactConfig] = None
    ):
        """Initialize executor agent.

        Args:
            llm_provider: Optional LLM provider
            kernel: Optional Kernel for tool calls (required for ReAct)
            react_config: Optional ReAct configuration (uses defaults if None)
        """
        super().__init__("Executor", llm_provider=llm_provider, kernel=kernel)

        # Prompt loader for YAML templates
        self._prompt_loader = get_prompt_loader()

        # Load ReAct config: parameter > config.yaml > defaults
        self.react_config = react_config or self._load_react_config()

        # Backward compatibility
        self.max_react_steps = self.react_config.max_steps

    def _load_react_config(self) -> ReactConfig:
        """Load ReAct configuration from config.yaml."""
        from core.config import load_config
        from core.utils import get_config_value

        config = load_config()
        react_dict = get_config_value(config, "react") or {}

        return ReactConfig(
            max_steps=react_dict.get("max_steps", 10),
            token_budget=react_dict.get("token_budget", 8000),
            token_warning_threshold=react_dict.get("token_warning_threshold", 0.8),
            max_consecutive_errors=react_dict.get("max_consecutive_errors", 3),
            repetition_window=react_dict.get("repetition_window", 5),
            enable_summarization=react_dict.get("enable_summarization", True)
        )

    def get_system_prompt(self) -> str:
        """Get execution-specific system prompt from YAML template."""
        prompt_loader = get_prompt_loader()
        return prompt_loader.get("executor.system")

    async def execute(self, context: TaskContext) -> ExecutionResult:
        """Execute task using ReAct loop if kernel available, else direct."""
        run_id = context.run_id or "unknown"

        with contextualize(run_id=run_id, agent="ExecutorAgent"):
            prompt_preview = context.prompt[:50] + "..." if len(context.prompt) > 50 else context.prompt
            logger.info(f"Execution started for task: '{prompt_preview}'")

            try:
                # Check if there's a plan to follow
                plan = context.metadata.get("plan")
                if plan:
                    return await self._execute_with_plan(context, plan)

                # Use ReAct loop if kernel is available
                if self.kernel:
                    return await self._execute_react(context)
                else:
                    return await self._execute_directly(context)

            except Exception as e:
                logger.error(f"Execution failed: {str(e)}")
                return ExecutionResult(
                    success=False,
                    response="",
                    error=f"Execution failed: {str(e)}"
                )

    async def _execute_react(self, context: TaskContext) -> ExecutionResult:
        """Execute task using internal ReAct loop with improvements.

        ReAct Pattern:
        1. Think: LLM reasons about the task
        2. Act: LLM decides to call tools
        3. Observe: Tool results are fed back to LLM
        4. Repeat until done or limits reached

        Improvements:
        - Token budget management
        - Repetition detection
        - Error circuit breaker
        - Configurable limits
        """
        start_time = time.time()
        current_step = 0
        all_tool_calls: List[ToolCall] = []

        # Get effective config (supports context override)
        config = self._get_effective_config(context)

        # Token tracking
        total_tokens_used = 0

        # Error tracking for circuit breaker
        consecutive_errors = 0

        # Repetition detection
        recent_calls: deque[ToolCallSignature] = deque(maxlen=config.repetition_window)

        # Build initial message history
        local_messages: List[Dict[str, Any]] = [
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": context.prompt}
        ]

        # Get tool definitions from kernel
        tool_definitions = self.kernel.get_tool_definitions()

        logger.info(f"Starting ReAct loop (max {config.max_steps} steps, token budget {config.token_budget})")

        while current_step < config.max_steps:
            current_step += 1
            logger.info(f"[ReAct] Step {current_step}/{config.max_steps}")

            # === Token budget check ===
            if total_tokens_used >= config.token_budget:
                logger.warning(f"Token budget exhausted ({total_tokens_used}/{config.token_budget})")
                break

            # Token warning and summarization
            if total_tokens_used >= config.token_budget * config.token_warning_threshold:
                logger.warning(f"Token usage at {total_tokens_used}/{config.token_budget} ({total_tokens_used/config.token_budget:.0%})")
                if config.enable_summarization:
                    local_messages = self._summarize_messages(local_messages)

            # === Circuit breaker check ===
            if consecutive_errors >= config.max_consecutive_errors:
                logger.error(f"Circuit breaker triggered: {consecutive_errors} consecutive errors")
                return ExecutionResult(
                    success=False,
                    response="",
                    error=f"Execution halted: {consecutive_errors} consecutive tool failures",
                    tool_calls=all_tool_calls,
                    metadata={
                        "agent": "executor",
                        "execution_time_ms": (time.time() - start_time) * 1000,
                        "react_steps": current_step,
                        "total_tokens": total_tokens_used,
                        "termination_reason": "circuit_breaker"
                    }
                )

            # --- THINK: Call LLM with tools ---
            logger.info("Thinking...")
            llm_response = await self.llm.generate(
                messages=local_messages,
                tools=tool_definitions if tool_definitions else None
            )

            # === Track token usage ===
            if llm_response.usage:
                step_tokens = llm_response.usage.get("total_tokens", 0)
                total_tokens_used += step_tokens
                logger.info(f"[ReAct] Token usage: +{step_tokens}, total: {total_tokens_used}/{config.token_budget}")

            thought = llm_response.content or ""
            tool_call_requests = llm_response.tool_calls

            # Log the thought
            if thought:
                thought_preview = thought[:100] + "..." if len(thought) > 100 else thought
                logger.info(f"Thought: {thought_preview}")

            # Add assistant message to history
            assistant_msg: Dict[str, Any] = {"role": "assistant", "content": thought}
            if tool_call_requests:
                # OpenAI format tool_calls
                assistant_msg["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in tool_call_requests
                ]
            local_messages.append(assistant_msg)

            # --- CHECK TERMINATION ---
            if not tool_call_requests:
                logger.info("No tool calls requested. Finishing ReAct loop.")
                break

            # Check for terminate tool
            terminate_requested = any(
                tc.function.name == "terminate"
                for tc in tool_call_requests
            )
            if terminate_requested:
                logger.info("Terminate tool called. Finishing ReAct loop.")
                break

            # --- ACT: Execute tool calls ---
            for tool_call in tool_call_requests:
                tool_name = tool_call.function.name
                try:
                    tool_args = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    tool_args = {}

                # === Repetition detection ===
                call_signature = ToolCallSignature.from_tool_call(
                    tool_name,
                    tool_call.function.arguments
                )

                repetition_count = sum(1 for c in recent_calls if c == call_signature)
                if repetition_count >= 2:
                    logger.warning(f"Repetitive action detected: {tool_name} called {repetition_count + 1} times")
                    # Inject strategy change prompt
                    local_messages.append({
                        "role": "system",
                        "content": f"NOTICE: You have called '{tool_name}' with the same arguments {repetition_count + 1} times. "
                                   f"Consider trying a different approach or tool."
                    })

                recent_calls.append(call_signature)

                logger.info(f"Action: Calling tool '{tool_name}' with args: {tool_args}")

                # Execute via Kernel (workspace-aware)
                tool_start = time.time()
                try:
                    result = await self.kernel.call_tool(
                        tool_name=tool_name,
                        parameters=tool_args,
                        context=context  # Pass context with workspace_path
                    )
                    observation = str(result)
                    tool_error = None
                    consecutive_errors = 0  # Reset on success
                except Exception as e:
                    observation = f"Tool execution failed: {e}"
                    tool_error = str(e)
                    consecutive_errors += 1
                    logger.error(f"Tool '{tool_name}' failed: {e} (consecutive: {consecutive_errors})")

                tool_duration = (time.time() - tool_start) * 1000

                # Log observation
                obs_preview = observation[:100] + "..." if len(observation) > 100 else observation
                logger.info(f"Observation: {obs_preview}")

                # Record tool call
                all_tool_calls.append(ToolCall(
                    name=tool_name,
                    parameters=tool_args,
                    result=result if not tool_error else None,
                    error=tool_error,
                    duration_ms=tool_duration
                ))

                # Add tool result to history (OpenAI format)
                local_messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": observation
                })

        # Loop finished
        execution_time = (time.time() - start_time) * 1000

        # Determine termination reason
        termination_reason = "completed"
        if current_step >= config.max_steps:
            logger.warning(f"Reached max ReAct steps ({config.max_steps})")
            termination_reason = "max_steps"
        elif total_tokens_used >= config.token_budget:
            termination_reason = "token_budget"

        logger.info(f"ReAct loop completed in {execution_time:.0f}ms, {len(all_tool_calls)} tool calls, {total_tokens_used} tokens")

        # Get final response - request summary if thought is empty
        final_response = thought
        if not final_response or final_response.strip() == "":
            # Request final summary from LLM using YAML template
            logger.info("Generating final summary...")
            summary_prompt = self._prompt_loader.get("executor.final_summary")
            local_messages.append({
                "role": "user",
                "content": summary_prompt
            })
            summary_response = await self.llm.generate(messages=local_messages)
            final_response = summary_response.content or "Task completed."

        return ExecutionResult(
            success=True,
            response=final_response,
            tool_calls=all_tool_calls,
            metadata={
                "agent": "executor",
                "execution_time_ms": execution_time,
                "react_steps": current_step,
                "tool_count": len(all_tool_calls),
                "total_tokens": total_tokens_used,
                "termination_reason": termination_reason,
                "workspace": str(context.workspace_path) if context.workspace_path else None
            }
        )

    def _get_effective_config(self, context: TaskContext) -> ReactConfig:
        """Get effective ReAct config (supports context override)."""
        base_config = self.react_config

        # Get overrides from context.metadata
        overrides = context.metadata.get("react_config", {})
        if not overrides:
            return base_config

        # Merge overrides
        return ReactConfig(
            max_steps=overrides.get("max_steps", base_config.max_steps),
            token_budget=overrides.get("token_budget", base_config.token_budget),
            token_warning_threshold=overrides.get("token_warning_threshold", base_config.token_warning_threshold),
            max_consecutive_errors=overrides.get("max_consecutive_errors", base_config.max_consecutive_errors),
            repetition_window=overrides.get("repetition_window", base_config.repetition_window),
            enable_summarization=overrides.get("enable_summarization", base_config.enable_summarization)
        )

    def _summarize_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Summarize message history to control token usage.

        Strategy: Keep system + original user + summary + recent 2 messages.
        Simple but effective - follows Linus principle.
        """
        if len(messages) <= 4:
            return messages

        # Preserve: system (index 0) + original user (index 1)
        preserved = [messages[0], messages[1]]
        recent = messages[-2:]  # Keep recent messages

        # Summarize middle messages
        middle_count = len(messages) - 4
        if middle_count > 0:
            summary_msg = {
                "role": "system",
                "content": f"[{middle_count} intermediate messages summarized to save tokens]"
            }
            preserved.append(summary_msg)

        preserved.extend(recent)

        logger.info(f"Message history summarized: {len(messages)} -> {len(preserved)} messages")
        return preserved

    async def _execute_directly(self, context: TaskContext) -> ExecutionResult:
        """Execute task directly without ReAct loop (fallback)."""
        start_time = time.time()

        # Build execution prompt from YAML template
        tools = ', '.join(context.tools) if context.tools else 'Standard tools'
        exec_template = self._prompt_loader.get("executor.direct_execute")
        exec_prompt = exec_template.format(task=context.prompt, tools=tools)

        # ReAct: Thinking phase
        logger.info("Thinking...")

        # Get response from LLM
        response = await self._call_llm(exec_prompt, context)

        # ReAct: Log the thought/response
        thought_preview = response[:100] + "..." if len(response) > 100 else response
        logger.info(f"Thought: {thought_preview}")

        # Extract and execute tool calls (legacy pattern matching)
        tool_calls = self._extract_tool_calls(response)
        tool_results = []

        if tool_calls:
            logger.info(f"Identified {len(tool_calls)} tool call(s)")
            tool_results = await self._execute_tool_calls(tool_calls, context)

        # Calculate execution time
        execution_time = (time.time() - start_time) * 1000
        logger.info(f"Execution completed in {execution_time:.0f}ms")

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
                "tool_count": len(tool_calls),
                "mode": "direct"
            }
        )

    async def _execute_with_plan(self, context: TaskContext, plan) -> ExecutionResult:
        """Execute task following a plan.

        Args:
            context: Task context
            plan: Either a dict with 'steps' key, or a string plan
        """
        # Handle string plan - use ReAct mode instead
        if isinstance(plan, str):
            logger.info("Plan is text, using ReAct mode")
            # Store plan in context for reference
            context.metadata["plan_text"] = plan
            if self.kernel:
                return await self._execute_react(context)
            else:
                return await self._execute_directly(context)

        steps_count = len(plan.get("steps", []))
        logger.info(f"Executing with plan: {steps_count} steps")

        results = []
        overall_success = True

        for step in plan.get("steps", []):
            step_num = step.get('number')
            step_desc = step.get('description', '')[:50]
            logger.info(f"[Executor] Executing step {step_num}: {step_desc}")

            # Execute each step
            step_result = await self._execute_step(context, step)
            results.append(step_result)

            if not step_result["success"]:
                overall_success = False
                logger.warning(f"Step {step_num} failed")
                break

        # Compile final response
        response = self._compile_results(results)
        logger.info(f"Plan execution completed. Success: {overall_success}")

        return ExecutionResult(
            success=overall_success,
            response=response,
            metadata={
                "agent": "executor",
                "plan_steps": steps_count,
                "executed_steps": len(results),
                "with_plan": True
            }
        )

    async def _execute_step(self, context: TaskContext, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single step from the plan."""
        try:
            # Build step prompt from YAML template
            step_template = self._prompt_loader.get("executor.step_execute")
            step_prompt = step_template.format(
                description=step.get('description', ''),
                details=' '.join(step.get('details', []))
            )

            # Execute
            response = await self._call_llm(step_prompt, context)

            # Check for tool calls
            tool_calls = self._extract_tool_calls(response)
            if tool_calls:
                await self._execute_tool_calls(tool_calls, context)

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

    async def _execute_tool_calls(
        self,
        tool_calls: List[Dict[str, Any]],
        context: Optional[TaskContext] = None
    ) -> List[Dict[str, Any]]:
        """Execute tool calls (legacy or via kernel)."""
        results = []

        for tool_call in tool_calls:
            tool_name = tool_call["name"]
            tool_params = tool_call["parameters"]
            start_time = time.time()

            # ReAct: Action phase
            logger.info(f"Action: Call tool '{tool_name}' with args: {tool_params}")

            try:
                # Prefer kernel if available
                if self.kernel and context:
                    result = await self.kernel.call_tool(
                        tool_name=tool_name,
                        parameters=tool_params,
                        context=context
                    )
                else:
                    # Fallback to tool_manager
                    tool = self.tool_manager.get_tool(tool_name)
                    if tool:
                        result = await tool.execute(**tool_params)
                    else:
                        raise ValueError(f"Tool {tool_name} not found")

                duration = (time.time() - start_time) * 1000

                # ReAct: Observation phase
                result_preview = str(result)[:100] + "..." if len(str(result)) > 100 else str(result)
                logger.info(f"Observation: Tool '{tool_name}' returned: {result_preview}")

                results.append({
                    "success": True,
                    "result": result,
                    "duration_ms": duration
                })

            except Exception as e:
                logger.error(f"Observation: Tool '{tool_name}' failed: {str(e)}")
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
                response_parts.append(f"Step {result['step']}: Completed - {result.get('response', '')[:100]}")
            else:
                response_parts.append(f"Step {result['step']}: Failed - {result.get('error', 'Unknown error')}")

        return "\n".join(response_parts)

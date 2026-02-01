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
from core.logger import log, contextualize
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
            token_budget=react_dict.get("token_budget", 15000),  # Summarization threshold, not hard limit
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
            log.info(f"Execution started for task: '{prompt_preview}'")

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
                log.error(f"Execution failed: {str(e)}")
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

        # Text-only output tracking (for guided prompting)
        consecutive_text_only = 0
        MAX_TEXT_ONLY_STEPS = 2  # Allow 2 thinking steps before stronger guidance

        # Build initial message history with conversation context
        local_messages: List[Dict[str, Any]] = [
            {"role": "system", "content": self.get_system_prompt()}
        ]

        # ========== INJECT COLLECTED USER INFO (for revisions) ==========
        # Prevents re-asking the same questions across revision loops
        collected_info = context.metadata.get("collected_user_info", [])
        if collected_info:
            # Build a structured, categorized summary
            info_text = """## ⚠️ CRITICAL: KNOWN FACTS (DO NOT ASK AGAIN)

The user has ALREADY provided the following information in previous interactions.
You MUST use these facts directly. DO NOT ask about any of these topics again.

### CONFIRMED FACTS:
"""
            # Categorize answers by common travel topics
            categories = {
                "dates": [],
                "travelers": [],
                "budget": [],
                "location": [],
                "preferences": [],
                "other": []
            }

            for item in collected_info:
                q = item.get("question", "").lower()
                a = item.get("answer", "")

                # Categorize based on keywords
                if any(k in q for k in ["date", "when", "時間", "日期", "april", "march"]):
                    categories["dates"].append(a)
                elif any(k in q for k in ["traveler", "people", "person", "人數", "幾個人"]):
                    categories["travelers"].append(a)
                elif any(k in q for k in ["budget", "cost", "price", "預算", "花費"]):
                    categories["budget"].append(a)
                elif any(k in q for k in ["city", "depart", "from", "出發", "城市", "taipei"]):
                    categories["location"].append(a)
                elif any(k in q for k in ["prefer", "like", "want", "喜歡", "偏好", "accommodation"]):
                    categories["preferences"].append(a)
                else:
                    categories["other"].append(f"{item.get('question', 'Q')}: {a}")

            # Output categorized facts
            if categories["dates"]:
                info_text += f"- **Travel Dates**: {', '.join(categories['dates'])}\n"
            if categories["travelers"]:
                info_text += f"- **Number of Travelers**: {', '.join(categories['travelers'])}\n"
            if categories["budget"]:
                info_text += f"- **Budget**: {', '.join(categories['budget'])}\n"
            if categories["location"]:
                info_text += f"- **Departure City**: {', '.join(categories['location'])}\n"
            if categories["preferences"]:
                info_text += f"- **Preferences**: {', '.join(categories['preferences'])}\n"
            if categories["other"]:
                for item in categories["other"]:
                    info_text += f"- {item}\n"

            info_text += """
### RULES:
1. Use the facts above directly - DO NOT ask for them again
2. If user says "之前問過了" or "already answered", CHECK THIS LIST
3. Only ask NEW questions about topics NOT covered above
"""

            local_messages.append({
                "role": "system",
                "content": info_text
            })
            log.info(f"[ReAct] Injected {len(collected_info)} previously collected user answers")

        # ========== INJECT REVISION INSTRUCTIONS (reviewer feedback) ==========
        revision_instructions = context.metadata.get("revision_instructions")
        if revision_instructions:
            local_messages.append({
                "role": "system",
                "content": f"IMPORTANT - Previous attempt was REJECTED. You must fix these issues:\n{revision_instructions}"
            })
            log.info("[ReAct] Injected revision instructions from reviewer")
        # ========== END INJECT REVISION INSTRUCTIONS ==========

        # ========== INJECT OKR GOALS (domain-specific) ==========
        # Philosophy: Define WHAT to achieve, not HOW. Let AI decide the path.
        domain = context.metadata.get("domain_schema")
        okr_prompt = context.metadata.get("okr_prompt")
        if domain and okr_prompt:
            local_messages.append({
                "role": "system",
                "content": f"## DOMAIN: {domain.upper()}\n\n{okr_prompt}"
            })
            log.info(f"[ReAct] Injected OKR goals for domain: {domain}")
        # ========== END INJECT OKR GOALS ==========

        # ========== INJECT USER DELEGATION FLAG ==========
        # When user explicitly delegates, executor should make autonomous decisions
        user_delegates = context.metadata.get("user_delegates", False)
        if user_delegates:
            local_messages.append({
                "role": "system",
                "content": (
                    "## USER DELEGATION ACTIVE\n\n"
                    "The user has explicitly delegated decision-making to you. "
                    "DO NOT ask for preferences on every detail. "
                    "Make reasonable, informed decisions and proceed autonomously. "
                    "Only ask questions for truly essential missing information."
                )
            })
            log.info("[ReAct] User delegation active - executor will be autonomous")
        # ========== END INJECT USER DELEGATION ==========

        # Add history from context.messages (cross-request memory)
        # IMPORTANT: Filter out problematic message types to maintain valid OpenAI message structure
        # OpenAI API requires: assistant(tool_calls) -> tool(tool_call_id) in matching sequence
        # We can't carry over tool interactions from previous executions as IDs won't match
        for msg in context.messages:
            if msg.role.value == "system":
                continue  # Skip system messages (we have our own)
            if msg.role.value == "tool":
                continue  # Skip tool messages (orphaned from previous executions)

            # For assistant messages, check if they have tool_calls (skip if so)
            if msg.role.value == "assistant" and msg.metadata and msg.metadata.get("tool_calls"):
                continue  # Skip assistant messages with tool_calls (would create orphaned references)

            msg_dict = {
                "role": msg.role.value,
                "content": msg.content
            }
            local_messages.append(msg_dict)

        # Add current prompt
        local_messages.append({"role": "user", "content": context.prompt})

        # Get tool definitions from kernel (with domain-based filtering)
        tool_definitions = self.kernel.get_tool_definitions(context)

        log.info(f"Starting ReAct loop (max {config.max_steps} steps)")

        while current_step < config.max_steps:
            current_step += 1
            log.info(f"[ReAct] Step {current_step}/{config.max_steps}")

            # === Token tracking (no hard limit - trust model's native context window) ===
            # Claude Code / Cursor pattern: warn and auto-summarize, don't hard-break
            if total_tokens_used >= config.token_budget * config.token_warning_threshold:
                log.info(f"[ReAct] Token usage: {total_tokens_used} (approaching summarization threshold)")
                if config.enable_summarization:
                    local_messages = self._summarize_messages(local_messages)

            # === Circuit breaker check ===
            if consecutive_errors >= config.max_consecutive_errors:
                log.error(f"Circuit breaker triggered: {consecutive_errors} consecutive errors")
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
            log.info("Thinking...")
            llm_response = await self.llm.generate(
                messages=local_messages,
                tools=tool_definitions if tool_definitions else None
            )

            # === Handle context_length_exceeded error ===
            # The LLM provider may return error as content instead of raising
            if llm_response.content and "context_length_exceeded" in llm_response.content:
                log.warning("[ReAct] Context length exceeded, triggering emergency summarization")
                local_messages = self._summarize_messages(local_messages)
                # Retry the call with summarized messages
                llm_response = await self.llm.generate(
                    messages=local_messages,
                    tools=tool_definitions if tool_definitions else None
                )

            # === Track token usage ===
            if llm_response.usage:
                step_tokens = llm_response.usage.get("total_tokens", 0)
                total_tokens_used += step_tokens
                log.info(f"[ReAct] Token usage: +{step_tokens}, total: {total_tokens_used}/{config.token_budget}")

            thought = llm_response.content or ""
            tool_call_requests = llm_response.tool_calls

            # Log the thought
            if thought:
                thought_preview = thought[:100] + "..." if len(thought) > 100 else thought
                log.info(f"Thought: {thought_preview}")

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
            # Check for terminate tool first
            if tool_call_requests:
                terminate_call = next(
                    (tc for tc in tool_call_requests if tc.function.name == "terminate"),
                    None
                )
                if terminate_call:
                    log.info("Terminate tool called. Finishing ReAct loop.")
                    # IMPORTANT: Add tool responses for ALL tool_calls to maintain OpenAI message integrity
                    # OpenAI API requires: assistant(tool_calls) -> tool(tool_call_id) pairing for EACH call
                    for tc in tool_call_requests:
                        if tc.function.name == "terminate":
                            local_messages.append({
                                "role": "tool",
                                "tool_call_id": tc.id,
                                "content": "Task completed. Terminating execution."
                            })
                        else:
                            # Other tools called alongside terminate - mark as skipped
                            local_messages.append({
                                "role": "tool",
                                "tool_call_id": tc.id,
                                "content": f"Skipped: terminate was called, {tc.function.name} not executed."
                            })
                    break
            else:
                # No tool calls - LLM output only text
                # Allow thinking steps, but guide towards action
                consecutive_text_only += 1

                if consecutive_text_only <= MAX_TEXT_ONLY_STEPS:
                    # Gentle guidance - allow thinking
                    log.info(f"[ReAct] Thinking step {consecutive_text_only}/{MAX_TEXT_ONLY_STEPS} (no tool call)")
                    local_messages.append({
                        "role": "system",
                        "content": (
                            "You provided analysis. What would you like to do next?\n"
                            "- Need more information? → Use `websearch` or `ask_user`\n"
                            "- Ready to deliver results? → Use `terminate` with your final answer\n"
                            "- Need to process files? → Use appropriate file tools"
                        )
                    })
                else:
                    # Stronger guidance after multiple text-only outputs
                    log.info(f"[ReAct] Extended thinking ({consecutive_text_only} steps). Encouraging action.")
                    local_messages.append({
                        "role": "system",
                        "content": (
                            "You've been analyzing for a while. Time to take action:\n"
                            "- If you have enough information → Call `terminate` with your answer\n"
                            "- If you need more data → Call a tool to gather it\n"
                            "Please proceed with a tool call."
                        )
                    })
                # Continue loop
                continue

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
                if repetition_count >= 1:
                    # Block repeated identical calls - this is a prompt/reasoning failure
                    log.warning(f"[ReAct] BLOCKED: Identical {tool_name} call detected (attempt {repetition_count + 1})")
                    observation = (
                        f"ERROR: You already called {tool_name} with these exact arguments. "
                        f"Repeating the same search will NOT give different results. "
                        f"You MUST either: (1) modify your search query, (2) use the results you already have, "
                        f"or (3) try a different tool."
                    )
                    tool_error = "DUPLICATE_CALL_BLOCKED"
                    tool_start = time.time()
                else:
                    recent_calls.append(call_signature)
                    log.info(f"Action: Calling tool '{tool_name}' with args: {tool_args}")

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
                        consecutive_text_only = 0  # Reset thinking counter on tool use
                    except Exception as e:
                        observation = f"Tool execution failed: {e}"
                        tool_error = str(e)
                        consecutive_errors += 1
                        log.error(f"Tool '{tool_name}' failed: {e} (consecutive: {consecutive_errors})")

                tool_duration = (time.time() - tool_start) * 1000

                # Log observation
                obs_preview = observation[:100] + "..." if len(observation) > 100 else observation
                log.info(f"Observation: {obs_preview}")

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

                # === System 1/2 Dynamic Assessment ===
                thinking_mode = self._assess_complexity(observation, tool_name, current_step)
                if thinking_mode == "system2":
                    log.info(f"[ReAct] Complex result detected → System 2 thinking")
                    system2_prompt = self._get_system2_prompt(tool_name, observation)
                    local_messages.append({
                        "role": "system",
                        "content": system2_prompt
                    })
                # System 1 continues normally without extra prompt

            # === After all tool calls, check if we need to summarize ===
            # This prevents context overflow on next iteration
            # Trigger earlier (12 messages ≈ 4-5 tool calls) to be more aggressive
            if len(local_messages) > 15 and config.enable_summarization:
                log.info(f"[ReAct] Messages: {len(local_messages)}, triggering proactive summarization")
                local_messages = self._summarize_messages(local_messages)

        # Loop finished
        execution_time = (time.time() - start_time) * 1000

        # Determine termination reason
        # Note: No token_budget termination - we trust model's native context limit
        termination_reason = "completed"
        if current_step >= config.max_steps:
            log.warning(f"Reached max ReAct steps ({config.max_steps})")
            termination_reason = "max_steps"

        log.info(f"ReAct loop completed in {execution_time:.0f}ms, {len(all_tool_calls)} tool calls, {total_tokens_used} tokens")

        # Get final response - request summary if thought is empty
        final_response = thought
        if not final_response or final_response.strip() == "":
            # Request final summary from LLM using YAML template
            log.info("Generating final summary...")
            # IMPORTANT: Clean messages before final summary to avoid tool_call pairing errors
            clean_messages = self._summarize_messages(local_messages)
            summary_prompt = self._prompt_loader.get("executor.final_summary")
            clean_messages.append({
                "role": "user",
                "content": summary_prompt
            })
            summary_response = await self.llm.generate(messages=clean_messages)
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

        Strategy:
        1. Always keep: system prompts
        2. Always keep: the first user message (original task)
        3. Keep recent messages with STRICT tool_call/tool pairing
        4. Truncate long tool responses to save tokens

        CRITICAL: OpenAI requires assistant(tool_calls) -> tool(tool_call_id) pairing.
        We must never have orphaned tool messages without their preceding assistant message.
        """
        if len(messages) <= 12:  # Don't summarize small histories
            return messages

        preserved = []

        # 1. Keep all system messages
        for msg in messages:
            if msg.get("role") == "system":
                preserved.append(msg)

        # 2. Keep the first user message
        first_user_msg = next((m for m in messages if m.get("role") == "user"), None)
        if first_user_msg and first_user_msg not in preserved:
            preserved.append(first_user_msg)

        # 3. Find the safe cut point - we need to keep tool_calls/tool pairs intact
        # Start from the end and work backwards to find complete pairs
        non_system_messages = [m for m in messages if m.get("role") != "system"]

        # Keep last N exchanges (an exchange = user/assistant + any tool calls/responses)
        max_recent = 10  # Keep roughly last 10 non-system messages
        recent_start_idx = max(0, len(non_system_messages) - max_recent)

        # Adjust start index to not break tool_call/tool pairing
        # If we're starting at a tool message, back up to find its assistant message
        while recent_start_idx > 0:
            msg = non_system_messages[recent_start_idx]
            if msg.get("role") == "tool":
                # This is a tool response - we need to include its assistant message
                recent_start_idx -= 1
            elif msg.get("role") == "assistant" and msg.get("tool_calls"):
                # Found an assistant with tool_calls - we need ALL its tool responses
                # Count how many tool_calls and ensure we have all responses
                break
            else:
                break

        recent_messages = non_system_messages[recent_start_idx:]

        # Truncate long tool observations
        for msg in recent_messages:
            if msg.get("role") == "tool":
                content = str(msg.get("content", ""))
                if len(content) > 500:
                    msg["content"] = content[:500] + "... [truncated]"

        # Add recent messages, avoiding duplicates
        for msg in recent_messages:
            if msg not in preserved:
                preserved.append(msg)

        # Final validation: ensure no orphaned tool messages
        validated = self._validate_tool_pairing(preserved)

        removed_count = len(messages) - len(validated)
        if removed_count > 0:
            log.info(f"Message history summarized: {len(messages)} -> {len(validated)} messages (removed {removed_count})")

        return validated

    def _validate_tool_pairing(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Ensure all tool messages have matching assistant tool_calls.

        OpenAI API requires strict pairing:
        - Every tool message must reference a tool_call_id from a preceding assistant message
        - Every assistant message with tool_calls must have corresponding tool responses
        """
        validated = []
        pending_tool_call_ids = set()

        for msg in messages:
            role = msg.get("role")

            if role == "assistant":
                # Track tool_call IDs from this assistant message
                tool_calls = msg.get("tool_calls", [])
                if tool_calls:
                    for tc in tool_calls:
                        tc_id = tc.get("id")
                        if tc_id:
                            pending_tool_call_ids.add(tc_id)
                validated.append(msg)

            elif role == "tool":
                # Only include tool messages that have matching tool_calls
                tool_call_id = msg.get("tool_call_id")
                if tool_call_id in pending_tool_call_ids:
                    validated.append(msg)
                    pending_tool_call_ids.discard(tool_call_id)
                # else: skip orphaned tool message

            else:
                # system, user messages pass through
                validated.append(msg)

        return validated

    def _assess_complexity(self, observation: str, tool_name: str, step: int) -> str:
        """Assess if the current situation requires System 2 (deep) thinking.

        System 1 (Fast): Simple tool results, clear next steps
        System 2 (Slow): Complex data, multiple options, errors, synthesis needed

        Returns: "system1" or "system2"
        """
        # Indicators that require System 2 thinking
        system2_indicators = [
            # Multiple results to synthesize
            len(observation) > 1500,
            # Error or failure
            "error" in observation.lower() or "failed" in observation.lower(),
            # Multiple options/choices
            observation.count("http") > 3,  # Multiple URLs to evaluate
            # Complex search results
            "search" in tool_name and len(observation) > 800,
            # User provided complex/ambiguous answer
            tool_name == "ask_user" and len(observation) > 100,
            # Late in execution (might need synthesis)
            step > 5,
        ]

        # If any indicator is true, use System 2
        if any(system2_indicators):
            return "system2"
        return "system1"

    def _get_system2_prompt(self, tool_name: str, observation: str) -> str:
        """Get System 2 deep thinking prompt based on situation."""
        base_prompt = """## 🧠 DEEP ANALYSIS REQUIRED

Before proceeding, take a moment to think carefully:

1. **What did we learn?** Summarize the key information from the tool result.
2. **What's still missing?** Identify gaps in our knowledge.
3. **What are the options?** List possible next steps.
4. **What's the best path?** Choose the most effective action.

"""
        if "search" in tool_name:
            return base_prompt + """For these search results:
- Which sources are most relevant?
- Is the information consistent or conflicting?
- Do we need more specific searches?
"""
        elif tool_name == "ask_user":
            return base_prompt + """For the user's response:
- Does this answer fully address our needs?
- Are there follow-up questions we should ask?
- How does this change our approach?
"""
        else:
            return base_prompt + """Consider:
- Did this tool achieve what we expected?
- What should we do next?
"""

    async def _execute_directly(self, context: TaskContext) -> ExecutionResult:
        """Execute task directly without ReAct loop (fallback)."""
        start_time = time.time()

        # Build execution prompt from YAML template
        tools = ', '.join(context.tools) if context.tools else 'Standard tools'
        exec_template = self._prompt_loader.get("executor.direct_execute")
        exec_prompt = exec_template.format(task=context.prompt, tools=tools)

        # ReAct: Thinking phase
        log.info("Thinking...")

        # Get response from LLM
        response = await self._call_llm(exec_prompt, context)

        # ReAct: Log the thought/response
        thought_preview = response[:100] + "..." if len(response) > 100 else response
        log.info(f"Thought: {thought_preview}")

        # Extract and execute tool calls (legacy pattern matching)
        tool_calls = self._extract_tool_calls(response)
        tool_results = []

        if tool_calls:
            log.info(f"Identified {len(tool_calls)} tool call(s)")
            tool_results = await self._execute_tool_calls(tool_calls, context)

        # Calculate execution time
        execution_time = (time.time() - start_time) * 1000
        log.info(f"Execution completed in {execution_time:.0f}ms")

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
            log.info("Plan is text, using ReAct mode")
            # Store plan in context for reference
            context.metadata["plan_text"] = plan
            if self.kernel:
                return await self._execute_react(context)
            else:
                return await self._execute_directly(context)

        steps_count = len(plan.get("steps", []))
        log.info(f"Executing with plan: {steps_count} steps")

        results = []
        overall_success = True

        for step in plan.get("steps", []):
            step_num = step.get('number')
            step_desc = step.get('description', '')[:50]
            log.info(f"[Executor] Executing step {step_num}: {step_desc}")

            # Execute each step
            step_result = await self._execute_step(context, step)
            results.append(step_result)

            if not step_result["success"]:
                overall_success = False
                log.warning(f"Step {step_num} failed")
                break

        # Compile final response
        response = self._compile_results(results)
        log.info(f"Plan execution completed. Success: {overall_success}")

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
            log.info(f"Action: Call tool '{tool_name}' with args: {tool_params}")

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
                log.info(f"Observation: Tool '{tool_name}' returned: {result_preview}")

                results.append({
                    "success": True,
                    "result": result,
                    "duration_ms": duration
                })

            except Exception as e:
                log.error(f"Observation: Tool '{tool_name}' failed: {str(e)}")
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

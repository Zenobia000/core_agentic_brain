"""Base agent class for specialized agents."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import time
from core.types import TaskContext, ExecutionResult, Message, MessageRole
# logger import removed - using simple_logger directly
from core.agent import Agent as CoreAgent
from core.llm import LLMProvider
from core.tools import ToolManager
from core.simple_logger import log, timer, set_trace


class BaseAgent(ABC):
    """Abstract base class for specialized agents."""

    def __init__(self, name: str = None, llm_provider: Optional[LLMProvider] = None):
        """Initialize base agent."""
        self.name = name or self.__class__.__name__
        # Create a default config for LLM if not provided
        from core.config import load_config
        config = load_config()

        # 消除特殊情況 - 統一處理
        from core.utils import get_config_value
        llm_config = get_config_value(config, "core", "llm") or \
                     get_config_value(config, "llm")
        tools_config = get_config_value(config, "core", "tools") or \
                       get_config_value(config, "tools")

        if llm_provider is None:
            self.llm = LLMProvider(llm_config)
        else:
            self.llm = llm_provider

        self.core_agent = CoreAgent(config)
        self.tool_manager = ToolManager(tools_config)
        log('agent.init', summary=f"{self.name} ready")

    @abstractmethod
    async def execute(self, context: TaskContext) -> ExecutionResult:
        """Execute the agent's specialized task."""
        pass

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Get the system prompt for this agent."""
        pass

    async def _call_llm(self, prompt: str, context: TaskContext) -> str:
        """Call LLM with agent-specific system prompt."""
        # Log the LLM call with 5W1H
        task_id = getattr(context, 'task_id', None)
        if not task_id:
            task_id = f"{self.name}_{int(time.time() * 1000)}"
            log('agent.start',
                agent=self.name,
                task=prompt[:100],  # First 100 chars as task description
                module=f'agents.{self.name.lower()}',
                strategy=getattr(context, 'strategy', 'direct'),
                complexity=getattr(context, 'complexity', 'unknown'),
                summary=f"{self.name} processing task"
            )
            context.task_id = task_id

        start_time = time.time()

        try:
            # Build messages
            messages = [
                Message(MessageRole.SYSTEM, self.get_system_prompt())
            ]

            # Add context messages if available
            messages.extend(context.messages)

            # Add current prompt
            messages.append(Message(MessageRole.USER, prompt))

            # Convert to dict format for LLM
            message_dicts = [
                {"role": msg.role.value, "content": msg.content}
                for msg in messages
            ]

            # Log the decision to call LLM
            log('agent.decision',
                agent=self.name,
                decision="Call LLM for processing",
                reasoning=f"Processing prompt: {prompt[:50]}...",
                task_id=task_id,
                summary=f"{self.name} calling LLM"
            )

            # Call LLM
            response = await self.llm.generate(message_dicts)

            log('debug', summary=f"{self.name} LLM response received")

            # Log successful completion
            duration_ms = (time.time() - start_time) * 1000
            log('agent.complete',
                agent=self.name,
                task_id=task_id,
                result=(response.content if hasattr(response, 'content') else str(response))[:200],
                duration_ms=duration_ms,
                summary=f"{self.name} completed in {duration_ms:.0f}ms"
            )

            # Return the content string from LLMResponse
            return response.content if hasattr(response, 'content') else str(response)

        except Exception as e:
            # Log error with context
            log('agent.error',
                agent=self.name,
                task_id=task_id,
                error=str(e),
                module=f'agents.{self.name.lower()}',
                action='llm_call',
                summary=f"{self.name} LLM call failed: {str(e)[:100]}"
            )
            log('error', summary=f"{self.name} LLM call failed", error=str(e))
            raise

    def _extract_tool_calls(self, response: str) -> List[Dict[str, Any]]:
        """Extract tool calls from LLM response."""
        tool_calls = []

        # Simple pattern matching for tool calls
        # Format: [TOOL: tool_name(param1=value1, param2=value2)]
        import re
        pattern = r'\[TOOL:\s*(\w+)\((.*?)\)\]'
        matches = re.findall(pattern, response)

        for tool_name, params_str in matches:
            params = {}
            if params_str:
                # Parse parameters
                param_pairs = params_str.split(',')
                for pair in param_pairs:
                    if '=' in pair:
                        key, value = pair.split('=', 1)
                        params[key.strip()] = value.strip().strip('"\'')

            tool_calls.append({
                "name": tool_name,
                "parameters": params
            })

        return tool_calls

    async def _execute_tools(self, tool_calls: List[Dict[str, Any]], task_id: str = None) -> List[Dict[str, Any]]:
        """Execute tool calls and return results."""
        results = []

        for tool_call in tool_calls:
            # Log tool usage with 5W1H
            if task_id:
                log('agent.tool_use',
                    agent=self.name,
                    tool=tool_call["name"],
                    parameters=tool_call["parameters"],
                    task_id=task_id,
                    summary=f"{self.name} using {tool_call['name']}"
                )

            try:
                tool = self.tool_manager.get_tool(tool_call["name"])
                if tool:
                    result = await tool.execute(**tool_call["parameters"])
                    results.append({
                        "tool": tool_call["name"],
                        "result": result,
                        "success": True
                    })
                else:
                    results.append({
                        "tool": tool_call["name"],
                        "error": f"Tool {tool_call['name']} not found",
                        "success": False
                    })
            except Exception as e:
                if task_id:
                    log('agent.error',
                        agent=self.name,
                        task_id=task_id,
                        error=str(e),
                        tool=tool_call["name"],
                        action='tool_execution',
                        summary=f"{self.name} tool {tool_call['name']} failed: {str(e)[:100]}"
                    )
                results.append({
                    "tool": tool_call["name"],
                    "error": str(e),
                    "success": False
                })

        return results
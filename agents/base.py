"""Base agent class for specialized agents."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TYPE_CHECKING
import time
from core.types import TaskContext, ExecutionResult, Message, MessageRole
from core.llm import LLMProvider
from core.tools import ToolManager
from core.logger import log

if TYPE_CHECKING:
    from core.kernel import Kernel


class BaseAgent(ABC):
    """Abstract base class for specialized agents."""

    def __init__(
        self,
        name: str = None,
        llm_provider: Optional[LLMProvider] = None,
        kernel: Optional["Kernel"] = None
    ):
        """Initialize base agent.

        Args:
            name: Agent name
            llm_provider: Optional LLM provider instance
            kernel: Optional Kernel instance for tool calls
        """
        self.name = name or self.__class__.__name__
        self.kernel = kernel  # Store kernel reference for tool calls

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

        self.tool_manager = ToolManager(tools_config)
        log.debug(f"Agent initialized: {self.name}")

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
            log.debug(f"{self.name} processing task: {prompt[:100]}")
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

            # Call LLM
            log.debug(f"{self.name} calling LLM")
            response = await self.llm.generate(message_dicts)

            # Log completion
            duration_ms = (time.time() - start_time) * 1000
            log.debug(f"{self.name} LLM response received in {duration_ms:.0f}ms")

            # Return the content string from LLMResponse
            return response.content if hasattr(response, 'content') else str(response)

        except Exception as e:
            log.error(f"{self.name} LLM call failed: {str(e)}")
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
            log.debug(f"{self.name} using tool: {tool_call['name']}")

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
                log.error(f"{self.name} tool {tool_call['name']} failed: {str(e)}")
                results.append({
                    "tool": tool_call["name"],
                    "error": str(e),
                    "success": False
                })

        return results
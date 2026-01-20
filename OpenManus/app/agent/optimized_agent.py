"""
Optimized Agent Implementation
Integrates Context Engineering Principles 1 & 2
"""

import asyncio
from typing import List, Optional, Set, Dict, Any, Union
from pydantic import Field

from app.agent.toolcall import ToolCallAgent
from app.memory_manager import EnhancedMemory, MemoryManager
from app.tool_manager import ToolRegistry, ToolStatus, TaskClassifier, ToolMask
from app.schema import Message, AgentState, ToolChoice, TOOL_CHOICE_TYPE
from app.tool import ToolCollection, BaseTool
from app.logger import logger
from app.prompt.toolcall import SYSTEM_PROMPT, NEXT_STEP_PROMPT


class OptimizedAgent(ToolCallAgent):
    """
    Optimized Agent implementing:
    - Principle 1: KV-Cache optimization with sliding window memory
    - Principle 2: Tool masking instead of direct modification
    """

    name: str = "optimized_agent"
    description: str = "An optimized agent with enhanced memory and tool management"

    # Enhanced components
    tool_registry: ToolRegistry = Field(default_factory=ToolRegistry)
    task_classifier: TaskClassifier = Field(default_factory=TaskClassifier)
    enhanced_memory: Optional[EnhancedMemory] = None

    # Configuration
    use_memory_optimization: bool = True
    use_tool_masking: bool = True
    memory_window_size: int = 20
    memory_summary_threshold: int = 30

    # User context
    user_permissions: Set[str] = Field(default_factory=set)
    task_context: Dict[str, Any] = Field(default_factory=dict)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Initialize enhanced memory if enabled
        if self.use_memory_optimization:
            self.enhanced_memory = MemoryManager.create_memory(
                strategy="enhanced",
                window_size=self.memory_window_size,
                summary_threshold=self.memory_summary_threshold
            )
            # Migrate existing messages if any
            if self.memory and self.memory.messages:
                self.enhanced_memory.messages = self.memory.messages.copy()
        else:
            self.enhanced_memory = None

        # Register existing tools in the registry if masking is enabled
        if self.use_tool_masking and hasattr(self, 'available_tools'):
            for tool in self.available_tools.tools:
                self.tool_registry.register_tool(
                    tool,
                    is_global=tool.name in self.special_tool_names
                )

    @property
    def messages(self) -> List[Message]:
        """Get messages for LLM context"""
        if self.use_memory_optimization and self.enhanced_memory:
            return self.enhanced_memory.get_context_messages()
        else:
            return self.memory.messages

    @messages.setter
    def messages(self, value: List[Message]) -> None:
        """Set messages"""
        if self.use_memory_optimization and self.enhanced_memory:
            self.enhanced_memory.messages = value
        else:
            self.memory.messages = value

    def add_message(self, message: Message) -> None:
        """Add a message to memory"""
        if self.use_memory_optimization and self.enhanced_memory:
            self.enhanced_memory.add_message(message)
        else:
            self.memory.add_message(message)

    def register_tool(self, tool: BaseTool, is_global: bool = False) -> None:
        """Register a tool in the registry"""
        if self.use_tool_masking:
            self.tool_registry.register_tool(tool, is_global)
        else:
            # Fallback to traditional approach
            if not hasattr(self, 'available_tools'):
                self.available_tools = ToolCollection()
            self.available_tools.tools.append(tool)

    def mask_tool(self, tool_name: str, status: ToolStatus, reason: Optional[str] = None) -> bool:
        """Apply masking to a tool"""
        if not self.use_tool_masking:
            logger.warning("Tool masking is disabled")
            return False

        return self.tool_registry.mask_tool(tool_name, status, reason)

    def set_user_permissions(self, permissions: Set[str]) -> None:
        """Set user permissions for tool access"""
        self.user_permissions = permissions

    def set_task_context(self, context: Dict[str, Any]) -> None:
        """Set task context for tool filtering"""
        self.task_context = context

    def configure_for_task(self, task_description: str) -> None:
        """
        Configure agent for a specific task type
        Uses TaskClassifier to optimize tool availability
        """
        if self.use_tool_masking:
            self.task_classifier.configure_registry_for_task(
                self.tool_registry,
                task_description
            )

    def get_available_tools_with_masking(self) -> ToolCollection:
        """Get tools with masking applied"""
        if self.use_tool_masking:
            return self.tool_registry.get_available_tools(
                self.user_permissions,
                self.task_context
            )
        else:
            return self.available_tools

    async def think(self) -> bool:
        """
        Enhanced think method with memory optimization and tool masking
        """
        # Add next step prompt if needed
        if self.next_step_prompt:
            user_msg = Message.user_message(self.next_step_prompt)
            self.add_message(user_msg)

        # Get messages with optimization
        messages = self.messages

        if not messages:
            logger.warning(f"Agent '{self.name}' has no messages to process")
            return False

        try:
            # Get tools with masking
            tools_to_use = self.get_available_tools_with_masking()

            # Log memory optimization status
            if self.use_memory_optimization and self.enhanced_memory and self.enhanced_memory.summary:
                logger.info(
                    f"📝 Using compressed memory: "
                    f"{self.enhanced_memory.summary.message_count} messages summarized, "
                    f"{len(messages)} in active window"
                )

            # Get response with tools
            response = await self.llm.ask_tool(
                messages=messages,
                system_msgs=(
                    [Message.system_message(self.system_prompt)]
                    if self.system_prompt
                    else None
                ),
                tools=tools_to_use.to_params(),
                tool_choice=self.tool_choices,
            )

            # Process response
            self.tool_calls = response.tool_calls if response and response.tool_calls else []
            content = response.content if response and response.content else ""

            # Log response
            logger.info(f"✨ {self.name}'s thoughts: {content}")
            if self.tool_calls:
                logger.info(f"🛠️ Selected {len(self.tool_calls)} tools")
                logger.info(f"🧰 Tools: {[call.function.name for call in self.tool_calls]}")

            # Handle response based on tool choice mode
            if self.tool_choices == ToolChoice.NONE:
                if content:
                    self.add_message(Message.assistant_message(content))
                    return True
                return False

            # Create and add assistant message
            assistant_msg = (
                Message.from_tool_calls(content=content, tool_calls=self.tool_calls)
                if self.tool_calls
                else Message.assistant_message(content)
            )
            self.add_message(assistant_msg)

            return bool(self.tool_calls or content)

        except Exception as e:
            logger.error(f"🚨 Error in think process: {e}")
            self.add_message(
                Message.assistant_message(f"Error encountered: {str(e)}")
            )
            return False

    async def act(self) -> str:
        """
        Execute tool calls with masking validation
        """
        if not self.tool_calls:
            if self.tool_choices == ToolChoice.REQUIRED:
                raise ValueError("Tool calls required but none provided")
            return self.messages[-1].content or "No content or commands to execute"

        results = []

        for command in self.tool_calls:
            tool_name = command.function.name

            # Validate tool is available with current masking
            if self.use_tool_masking:
                mask = self.tool_registry.get_tool_status(tool_name)
                if mask and mask.status == ToolStatus.DISABLED:
                    error_msg = f"Tool '{tool_name}' is currently disabled"
                    if mask.reason:
                        error_msg += f": {mask.reason}"
                    results.append(error_msg)
                    logger.warning(f"🚫 Attempted to use disabled tool: {tool_name}")
                    continue

            # Execute tool as normal
            result = await self.execute_tool(command)
            results.append(result)

            # Add tool result to memory
            tool_msg = Message.tool_message(
                result,
                tool_call_id=command.id,
                tool_name=tool_name
            )
            self.add_message(tool_msg)

            # Check for termination
            if tool_name in self.special_tool_names:
                self.state = AgentState.FINISHED

        return " | ".join(results)

    async def run(self) -> str:
        """
        Run the agent with optimizations
        """
        self.state = AgentState.RUNNING
        logger.info(f"🚀 Starting {self.name} with optimizations:")
        logger.info(f"  - Memory optimization: {self.use_memory_optimization}")
        logger.info(f"  - Tool masking: {self.use_tool_masking}")

        step = 0
        final_response = ""

        while self.state == AgentState.RUNNING and step < self.max_steps:
            step += 1
            logger.info(f"Executing step {step}/{self.max_steps}")

            # Think phase
            should_act = await self.think()

            if self.state == AgentState.FINISHED:
                break

            if should_act:
                # Act phase
                action_result = await self.act()
                final_response = action_result

                if self.state == AgentState.FINISHED:
                    break

        # Log memory statistics if optimization is enabled
        if self.use_memory_optimization and self.enhanced_memory:
            logger.info(
                f"📊 Memory stats: "
                f"{len(self.enhanced_memory.messages)} active, "
                f"{len(self.enhanced_memory.archived_messages)} archived"
            )

        return final_response

    def get_optimization_stats(self) -> Dict[str, Any]:
        """Get statistics about optimization performance"""
        stats = {
            "memory_optimization_enabled": self.use_memory_optimization,
            "tool_masking_enabled": self.use_tool_masking
        }

        if self.use_memory_optimization and self.enhanced_memory:
            stats.update({
                "active_messages": len(self.enhanced_memory.messages),
                "archived_messages": len(self.enhanced_memory.archived_messages),
                "has_summary": self.enhanced_memory.summary is not None,
                "summary_message_count": (
                    self.enhanced_memory.summary.message_count
                    if self.enhanced_memory.summary
                    else 0
                )
            })

        if self.use_tool_masking:
            all_tools = self.tool_registry.list_all_tools()
            stats.update({
                "total_tools_registered": len(all_tools),
                "enabled_tools": len([t for t in all_tools if t["status"] == ToolStatus.ENABLED]),
                "disabled_tools": len([t for t in all_tools if t["status"] == ToolStatus.DISABLED]),
                "restricted_tools": len([t for t in all_tools if t["status"] == ToolStatus.RESTRICTED])
            })

        return stats
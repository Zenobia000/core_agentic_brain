"""
Tool Manager for OpenManus Agent System
Implements Principle 2: Tool Masking instead of Direct Modification
"""

from typing import Dict, List, Set, Optional, Any, Union
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime

from app.tool.base import BaseTool
from app.tool import ToolCollection
from app.logger import logger


class ToolStatus(str, Enum):
    """Tool availability status"""
    ENABLED = "enabled"
    DISABLED = "disabled"
    RESTRICTED = "restricted"  # Requires special permissions
    UNAVAILABLE = "unavailable"  # Temporarily unavailable


class ToolMask(BaseModel):
    """Mask for a single tool"""

    tool_name: str
    status: ToolStatus = ToolStatus.ENABLED
    reason: Optional[str] = None
    disabled_at: Optional[datetime] = None
    permissions_required: List[str] = Field(default_factory=list)
    context_requirements: Dict[str, Any] = Field(default_factory=dict)


class ToolRegistry(BaseModel):
    """
    Central registry of all available tools
    Tools are never removed, only masked
    """

    _tools: Dict[str, BaseTool] = Field(default_factory=dict, alias="tools")
    _masks: Dict[str, ToolMask] = Field(default_factory=dict, alias="masks")
    _global_tools: Set[str] = Field(default_factory=set, description="Tools always available")

    model_config = {
        "arbitrary_types_allowed": True
    }

    def register_tool(self, tool: BaseTool, is_global: bool = False) -> None:
        """
        Register a tool in the registry
        Once registered, tools are never removed, only masked
        """
        tool_name = tool.name

        if tool_name in self._tools:
            logger.warning(f"Tool '{tool_name}' already registered, updating...")

        self._tools[tool_name] = tool
        self._masks[tool_name] = ToolMask(tool_name=tool_name)

        if is_global:
            self._global_tools.add(tool_name)

        logger.info(f"✅ Tool '{tool_name}' registered {'(global)' if is_global else ''}")

    def mask_tool(self, tool_name: str, status: ToolStatus, reason: Optional[str] = None) -> bool:
        """
        Apply a mask to a tool (enable/disable/restrict)
        Returns True if successful
        """
        if tool_name not in self._tools:
            logger.error(f"Tool '{tool_name}' not found in registry")
            return False

        if tool_name in self._global_tools and status != ToolStatus.ENABLED:
            logger.warning(f"Cannot mask global tool '{tool_name}'")
            return False

        mask = self._masks[tool_name]
        mask.status = status
        mask.reason = reason

        if status in [ToolStatus.DISABLED, ToolStatus.UNAVAILABLE]:
            mask.disabled_at = datetime.now()
        else:
            mask.disabled_at = None

        logger.info(f"🎭 Tool '{tool_name}' masked as {status} {f'({reason})' if reason else ''}")
        return True

    def set_tool_permissions(self, tool_name: str, permissions: List[str]) -> bool:
        """Set required permissions for a tool"""
        if tool_name not in self._tools:
            return False

        self._masks[tool_name].permissions_required = permissions
        return True

    def set_tool_context(self, tool_name: str, context_requirements: Dict[str, Any]) -> bool:
        """Set context requirements for a tool"""
        if tool_name not in self._tools:
            return False

        self._masks[tool_name].context_requirements = context_requirements
        return True

    def get_available_tools(
        self,
        user_permissions: Optional[Set[str]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> ToolCollection:
        """
        Get currently available tools based on masks, permissions, and context
        This is the key method that implements masking
        """
        available_tools = []

        for tool_name, tool in self._tools.items():
            mask = self._masks[tool_name]

            # Check if tool is enabled
            if mask.status == ToolStatus.DISABLED:
                continue

            # Check permissions
            if mask.permissions_required:
                if not user_permissions or not all(
                    perm in user_permissions for perm in mask.permissions_required
                ):
                    continue

            # Check context requirements
            if mask.context_requirements and context:
                if not self._check_context_requirements(context, mask.context_requirements):
                    continue

            # Add tool with status annotation if not fully enabled
            if mask.status != ToolStatus.ENABLED:
                # Clone tool and update description to indicate status
                modified_tool = self._annotate_tool_status(tool, mask)
                available_tools.append(modified_tool)
            else:
                available_tools.append(tool)

        return ToolCollection(*available_tools)

    def _check_context_requirements(self, context: Dict[str, Any], requirements: Dict[str, Any]) -> bool:
        """Check if context meets requirements"""
        for key, required_value in requirements.items():
            if key not in context:
                return False
            if context[key] != required_value:
                return False
        return True

    def _annotate_tool_status(self, tool: BaseTool, mask: ToolMask) -> BaseTool:
        """Create a modified tool with status annotation in description"""
        # Create a copy of the tool
        tool_copy = tool.model_copy()

        # Add status annotation to description
        status_note = f"\n[STATUS: {mask.status.upper()}"
        if mask.reason:
            status_note += f" - {mask.reason}"
        status_note += "]"

        tool_copy.description = tool.description + status_note

        return tool_copy

    def get_tool_status(self, tool_name: str) -> Optional[ToolMask]:
        """Get the current mask/status of a tool"""
        return self._masks.get(tool_name)

    def list_all_tools(self) -> List[Dict[str, Any]]:
        """List all registered tools with their current status"""
        tools_list = []
        for tool_name, tool in self._tools.items():
            mask = self._masks[tool_name]
            tools_list.append({
                "name": tool_name,
                "description": tool.description,
                "status": mask.status,
                "is_global": tool_name in self._global_tools,
                "reason": mask.reason,
                "permissions_required": mask.permissions_required,
                "context_requirements": mask.context_requirements
            })
        return tools_list


class EnhancedToolCallAgent:
    """
    Enhanced ToolCall Agent with Tool Masking support
    This is a mixin that can be applied to existing agents
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Initialize tool registry
        self.tool_registry = ToolRegistry()

        # Register existing tools
        if hasattr(self, 'available_tools'):
            for tool in self.available_tools.tools:
                self.tool_registry.register_tool(tool)

    def add_tool(self, tool: BaseTool, is_global: bool = False) -> None:
        """Add a tool to the registry (never removed, only masked)"""
        self.tool_registry.register_tool(tool, is_global)

    def enable_tool(self, tool_name: str) -> bool:
        """Enable a tool"""
        return self.tool_registry.mask_tool(tool_name, ToolStatus.ENABLED)

    def disable_tool(self, tool_name: str, reason: Optional[str] = None) -> bool:
        """Disable a tool with optional reason"""
        return self.tool_registry.mask_tool(tool_name, ToolStatus.DISABLED, reason)

    def restrict_tool(self, tool_name: str, permissions: List[str]) -> bool:
        """Restrict a tool to specific permissions"""
        if self.tool_registry.mask_tool(tool_name, ToolStatus.RESTRICTED):
            return self.tool_registry.set_tool_permissions(tool_name, permissions)
        return False

    def get_masked_tools(
        self,
        user_permissions: Optional[Set[str]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> ToolCollection:
        """
        Get available tools based on current masks and context
        This should be called in think() method instead of directly using available_tools
        """
        return self.tool_registry.get_available_tools(user_permissions, context)

    async def think_with_masking(
        self,
        user_permissions: Optional[Set[str]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Enhanced think method that applies tool masking
        This wraps the original think() method
        """
        # Store original tools
        original_tools = self.available_tools if hasattr(self, 'available_tools') else None

        try:
            # Apply masking
            self.available_tools = self.get_masked_tools(user_permissions, context)

            # Call original think method
            if hasattr(super(), 'think'):
                return await super().think()
            else:
                raise NotImplementedError("Parent class must implement think() method")

        finally:
            # Restore original tools (though with masking, this shouldn't be necessary)
            if original_tools is not None:
                self.available_tools = original_tools


class TaskClassifier(BaseModel):
    """
    Classify tasks and determine appropriate tool masks
    Helps determine which tools should be available for specific task types
    """

    task_types: Dict[str, List[str]] = Field(
        default_factory=lambda: {
            "code_generation": ["python_execute", "str_replace_editor", "file_create"],
            "web_research": ["web_search", "browser_use", "crawl4ai"],
            "data_analysis": ["python_execute", "pandas_tool", "plot_tool"],
            "system_admin": ["bash_execute", "file_operations", "process_manager"],
            "communication": ["email_tool", "slack_tool", "create_chat_completion"]
        },
        description="Mapping of task types to relevant tools"
    )

    def classify_task(self, task_description: str) -> str:
        """
        Classify a task based on its description
        Returns the task type
        """
        # Simple keyword-based classification (can be enhanced with ML)
        task_lower = task_description.lower()

        if any(keyword in task_lower for keyword in ["code", "program", "script", "function", "class"]):
            return "code_generation"
        elif any(keyword in task_lower for keyword in ["search", "web", "browse", "find online"]):
            return "web_research"
        elif any(keyword in task_lower for keyword in ["data", "analyze", "plot", "chart", "statistics"]):
            return "data_analysis"
        elif any(keyword in task_lower for keyword in ["system", "server", "process", "service"]):
            return "system_admin"
        elif any(keyword in task_lower for keyword in ["email", "message", "notify", "communicate"]):
            return "communication"
        else:
            return "general"

    def get_recommended_tools(self, task_type: str) -> List[str]:
        """Get recommended tools for a task type"""
        return self.task_types.get(task_type, [])

    def configure_registry_for_task(
        self,
        registry: ToolRegistry,
        task_description: str
    ) -> None:
        """
        Configure tool registry masks based on task classification
        """
        task_type = self.classify_task(task_description)
        recommended_tools = self.get_recommended_tools(task_type)

        # Enable recommended tools
        for tool_name in recommended_tools:
            registry.mask_tool(tool_name, ToolStatus.ENABLED)

        # Optionally restrict other tools (can be configured)
        all_tools = registry.list_all_tools()
        for tool_info in all_tools:
            if tool_info["name"] not in recommended_tools and not tool_info["is_global"]:
                # Don't disable, just mark as restricted for this context
                registry.mask_tool(
                    tool_info["name"],
                    ToolStatus.RESTRICTED,
                    f"Not recommended for {task_type} tasks"
                )

        logger.info(f"🎯 Registry configured for '{task_type}' task with {len(recommended_tools)} primary tools")
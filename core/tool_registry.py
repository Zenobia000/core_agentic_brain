"""
Tool Registry - Single source of truth for all tools

Linus: "One place to rule them all"
Design: Immutable after boot, runtime filtering via masking
"""

from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class ToolCategory(Enum):
    """Tool categories for filtering."""
    CORE = "core"       # Always available (terminate)
    FILE = "file"       # File operations (files)
    SEARCH = "search"   # Web/search operations (websearch)
    CODE = "code"       # Code execution (python)
    USER = "user"       # User interaction (ask_user)
    SYSTEM = "system"   # System operations (shell)


@dataclass
class ToolEntry:
    """Tool entry with metadata."""
    name: str
    definition: Dict[str, Any]
    category: ToolCategory
    requires_approval: bool = False
    permissions: Set[str] = field(default_factory=set)


class ToolRegistry:
    """
    Central registry for all tools.

    Invariants:
    - All tools are registered at boot time
    - Registry is immutable after freeze()
    - get_filtered() returns masked view, never modifies registry

    Usage:
        registry = get_tool_registry()
        # During boot
        registry.register("python", definition, ToolCategory.CODE)
        registry.freeze()

        # At runtime
        tools = registry.get_filtered(categories={ToolCategory.CODE})
    """

    def __init__(self):
        self._tools: Dict[str, ToolEntry] = {}
        self._frozen = False

    def register(
        self,
        name: str,
        definition: Dict[str, Any],
        category: ToolCategory = ToolCategory.CORE,
        requires_approval: bool = False,
        permissions: Optional[Set[str]] = None
    ) -> None:
        """
        Register a tool (only allowed before freeze).

        Args:
            name: Tool name
            definition: OpenAI function calling format
            category: Tool category for filtering
            requires_approval: Whether tool requires user approval
            permissions: Required permissions to use this tool
        """
        if self._frozen:
            raise RuntimeError(
                f"Registry is frozen, cannot register tool: {name}"
            )

        self._tools[name] = ToolEntry(
            name=name,
            definition=definition,
            category=category,
            requires_approval=requires_approval,
            permissions=permissions or set()
        )

    def freeze(self) -> None:
        """Freeze registry (no more registrations allowed)."""
        self._frozen = True

    @property
    def is_frozen(self) -> bool:
        """Check if registry is frozen."""
        return self._frozen

    def get_all(self) -> List[Dict[str, Any]]:
        """Get all tool definitions (full list)."""
        return [t.definition for t in self._tools.values()]

    def get_filtered(
        self,
        categories: Optional[Set[ToolCategory]] = None,
        exclude_names: Optional[Set[str]] = None,
        include_names: Optional[Set[str]] = None,
        user_permissions: Optional[Set[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get tool definitions with mask applied.

        Args:
            categories: Only include tools from these categories
            exclude_names: Exclude tools by name
            include_names: Only include tools by name (overrides categories)
            user_permissions: User's permission set for permission-gated tools

        Returns:
            Filtered list of tool definitions
        """
        result = []
        exclude = exclude_names or set()

        for tool in self._tools.values():
            # Explicit exclusion
            if tool.name in exclude:
                continue

            # Explicit inclusion (highest priority)
            if include_names is not None:
                if tool.name not in include_names:
                    continue
            else:
                # Category filter (only if no include_names)
                if categories and tool.category not in categories:
                    continue

            # Permission filter
            if tool.permissions:
                if not user_permissions or not tool.permissions.issubset(user_permissions):
                    continue

            result.append(tool.definition)

        return result

    def get_tool_names(self) -> List[str]:
        """Get all registered tool names."""
        return list(self._tools.keys())

    def has_tool(self, name: str) -> bool:
        """Check if tool is registered."""
        return name in self._tools

    def get_tool_category(self, name: str) -> Optional[ToolCategory]:
        """Get category for a tool."""
        entry = self._tools.get(name)
        return entry.category if entry else None


# Singleton instance
_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """Get singleton ToolRegistry instance."""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry


def reset_tool_registry() -> None:
    """Reset singleton (for testing only)."""
    global _registry
    _registry = None

"""
NEXA Tool Registry — Auto-discovers and manages all available tools.
"""

from __future__ import annotations

from typing import Any, Optional

from loguru import logger

from app.tools.base import Tool, ToolResult


class ToolRegistry:
    """
    Central registry for all NEXA tools.
    
    Tools register themselves here and the agent uses the registry
    to discover, select, and execute tools.
    """

    def __init__(self):
        self._tools: dict[str, Tool] = {}
        logger.info("Tool registry initialized")

    def register(self, tool: Tool):
        """Register a tool instance."""
        if tool.name in self._tools:
            logger.warning(f"Tool already registered, overwriting: {tool.name}")
        self._tools[tool.name] = tool
        logger.info(
            f"Registered tool: {tool.name} "
            f"[{tool.category.value}] "
            f"(risk: {tool.permission_level.value})"
        )

    def get(self, name: str) -> Optional[Tool]:
        """Get a tool by name."""
        return self._tools.get(name)

    def has(self, name: str) -> bool:
        """Check if a tool exists."""
        return name in self._tools

    def list_all(self) -> list[dict[str, Any]]:
        """List all registered tools."""
        return [tool.to_info() for tool in self._tools.values()]

    def list_names(self) -> list[str]:
        """List all tool names."""
        return list(self._tools.keys())

    def list_by_category(self, category: str) -> list[dict[str, Any]]:
        """List tools in a specific category."""
        return [
            tool.to_info()
            for tool in self._tools.values()
            if tool.category.value == category
        ]

    def search(self, query: str) -> list[dict[str, Any]]:
        """Search tools by name or description."""
        query_lower = query.lower()
        results = []
        for tool in self._tools.values():
            if (
                query_lower in tool.name.lower()
                or query_lower in tool.description.lower()
            ):
                results.append(tool.to_info())
        return results

    def get_llm_tools(self) -> list[dict[str, Any]]:
        """Get all tools in LLM function-calling format."""
        return [tool.to_llm_schema() for tool in self._tools.values()]

    def get_tool_descriptions(self) -> str:
        """Get a formatted string of all tool descriptions for the LLM prompt."""
        lines = []
        for tool in sorted(self._tools.values(), key=lambda t: t.name):
            params = ", ".join(
                f"{p.name}: {p.type}" for p in tool.parameters
            )
            lines.append(
                f"- {tool.name}({params}): {tool.description} "
                f"[risk: {tool.permission_level.value}]"
            )
        return "\n".join(lines)

    @property
    def count(self) -> int:
        return len(self._tools)


def discover_and_register_tools(registry: ToolRegistry):
    """
    Auto-discover and register all built-in tools.
    Import each tool module to trigger registration.
    """
    logger.info("Discovering tools...")

    # Import tool modules — each module registers its tools
    from app.tools.computer import screen, mouse, keyboard, clipboard
    from app.tools.os_tools import system, windows, apps
    from app.tools.filesystem import operations
    from app.tools.browser import browser_tools
    from app.tools.android import android_tools

    # Collect all tool classes from modules
    tool_modules = [
        screen, mouse, keyboard, clipboard,
        system, windows, apps,
        operations,
        browser_tools,
        android_tools,
    ]

    for module in tool_modules:
        if hasattr(module, "get_tools"):
            for tool in module.get_tools():
                registry.register(tool)

    logger.info(f"Tool discovery complete: {registry.count} tools registered")

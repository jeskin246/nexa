"""
NEXA Agent Observer — Captures environment state after actions.
"""

from __future__ import annotations

from typing import Any, Optional

from loguru import logger

from app.tools.base import ToolResult
from app.tools.registry import ToolRegistry


class Observer:
    """
    Observes the environment after tool execution.
    
    Can capture:
    - Screen state (screenshots)
    - Application state
    - File system changes
    - Browser state
    """

    def __init__(self, registry: ToolRegistry):
        self._registry = registry

    async def observe_screen(self) -> Optional[str]:
        """Capture current screen state."""
        screen_tool = self._registry.get("screen.capture")
        if screen_tool:
            try:
                result = await screen_tool.execute()
                if result.success and result.artifacts:
                    return result.artifacts[0]  # screenshot path
            except Exception as e:
                logger.warning(f"Screen observation failed: {e}")
        return None

    async def observe_active_window(self) -> Optional[str]:
        """Get the currently active window title."""
        windows_tool = self._registry.get("os.windows")
        if windows_tool:
            try:
                result = await windows_tool.execute(action="active")
                if result.success:
                    return str(result.data)
            except Exception as e:
                logger.warning(f"Window observation failed: {e}")
        return None

    async def observe_after_action(
        self,
        tool_name: str,
        result: ToolResult,
    ) -> dict[str, Any]:
        """
        Observe the environment after a tool execution.
        Returns a dict of observations for the agent to reason about.
        """
        observations: dict[str, Any] = {
            "tool_result": {
                "success": result.success,
                "data": str(result.data)[:1000] if result.data else None,
                "error": result.error,
                "message": result.message,
            }
        }

        # For UI-affecting tools, observe the screen
        ui_tools = {"mouse.", "keyboard.", "browser.", "app."}
        if any(tool_name.startswith(prefix) for prefix in ui_tools):
            active_window = await self.observe_active_window()
            if active_window:
                observations["active_window"] = active_window

        # For filesystem tools, note any created artifacts
        if result.artifacts:
            observations["artifacts"] = result.artifacts

        logger.debug(f"Observations after {tool_name}: {list(observations.keys())}")
        return observations

    async def get_environment_summary(self) -> dict[str, Any]:
        """Get a summary of the current environment state."""
        summary: dict[str, Any] = {}

        # Active window
        active_window = await self.observe_active_window()
        if active_window:
            summary["active_window"] = active_window

        # System info
        sys_tool = self._registry.get("os.system_info")
        if sys_tool:
            try:
                result = await sys_tool.execute()
                if result.success:
                    summary["system"] = result.data
            except Exception:
                pass

        return summary

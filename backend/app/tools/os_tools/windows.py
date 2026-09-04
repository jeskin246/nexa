"""
NEXA OS Tools — Window management.
"""

from __future__ import annotations

from typing import Any

from loguru import logger

from app.security.permissions import PermissionLevel
from app.tools.base import Tool, ToolParameter, ToolResult


class WindowsTool(Tool):
    @property
    def name(self) -> str:
        return "os.windows"

    @property
    def description(self) -> str:
        return (
            "Manage desktop windows: list all windows, get active window, "
            "focus a window, minimize, maximize, or close windows."
        )

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="action", type="string",
                description="Action to perform",
                enum=["list", "active", "focus", "minimize", "maximize", "close"],
            ),
            ToolParameter(
                name="title", type="string",
                description="Window title to match (partial match, case-insensitive)",
                required=False,
            ),
        ]

    @property
    def permission_level(self) -> PermissionLevel:
        return PermissionLevel.LOW

    async def execute(self, **params: Any) -> ToolResult:
        try:
            import pygetwindow as gw
            
            action = params.get("action", "list")
            title = params.get("title", "")

            if action == "list":
                windows = []
                for w in gw.getAllWindows():
                    if w.title and w.title.strip():
                        windows.append({
                            "title": w.title,
                            "left": w.left,
                            "top": w.top,
                            "width": w.width,
                            "height": w.height,
                            "visible": w.visible,
                            "minimized": w.isMinimized,
                            "maximized": w.isMaximized,
                        })
                return ToolResult.ok(
                    data={"windows": windows, "count": len(windows)},
                    message=f"Found {len(windows)} windows",
                )

            elif action == "active":
                active = gw.getActiveWindow()
                if active:
                    return ToolResult.ok(
                        data={
                            "title": active.title,
                            "left": active.left,
                            "top": active.top,
                            "width": active.width,
                            "height": active.height,
                        },
                        message=f"Active window: {active.title}",
                    )
                return ToolResult.ok(
                    data={"title": None},
                    message="No active window",
                )

            elif action in ("focus", "minimize", "maximize", "close"):
                if not title:
                    return ToolResult.fail("Window title required for this action")
                
                matching = [
                    w for w in gw.getAllWindows()
                    if title.lower() in w.title.lower() and w.title.strip()
                ]
                
                if not matching:
                    return ToolResult.fail(f"No window matching: {title}")
                
                window = matching[0]
                
                if action == "focus":
                    window.activate()
                    msg = f"Focused window: {window.title}"
                elif action == "minimize":
                    window.minimize()
                    msg = f"Minimized: {window.title}"
                elif action == "maximize":
                    window.maximize()
                    msg = f"Maximized: {window.title}"
                elif action == "close":
                    window.close()
                    msg = f"Closed: {window.title}"
                
                logger.info(msg)
                return ToolResult.ok(message=msg)

            else:
                return ToolResult.fail(f"Unknown action: {action}")

        except Exception as e:
            return ToolResult.fail(str(e))


def get_tools() -> list[Tool]:
    return [WindowsTool()]

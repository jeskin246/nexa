"""
NEXA Computer Tools — Mouse control.
"""

from __future__ import annotations

from typing import Any

from loguru import logger

from app.security.permissions import PermissionLevel
from app.tools.base import Tool, ToolParameter, ToolResult


class MouseMoveTool(Tool):
    @property
    def name(self) -> str:
        return "mouse.move"

    @property
    def description(self) -> str:
        return "Move the mouse cursor to specified screen coordinates."

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(name="x", type="integer", description="X coordinate"),
            ToolParameter(name="y", type="integer", description="Y coordinate"),
            ToolParameter(
                name="duration",
                type="number",
                description="Movement duration in seconds",
                required=False,
                default=0.3,
            ),
        ]

    @property
    def permission_level(self) -> PermissionLevel:
        return PermissionLevel.MEDIUM

    async def execute(self, **params: Any) -> ToolResult:
        try:
            import pyautogui
            pyautogui.FAILSAFE = True
            
            x = params.get("x", 0)
            y = params.get("y", 0)
            duration = params.get("duration", 0.3)
            
            pyautogui.moveTo(x, y, duration=duration)
            logger.info(f"Mouse moved to ({x}, {y})")
            
            return ToolResult.ok(
                data={"x": x, "y": y},
                message=f"Mouse moved to ({x}, {y})",
            )
        except Exception as e:
            return ToolResult.fail(str(e))


class MouseClickTool(Tool):
    @property
    def name(self) -> str:
        return "mouse.click"

    @property
    def description(self) -> str:
        return "Click the mouse at specified coordinates or current position."

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="x", type="integer",
                description="X coordinate (optional, uses current position if omitted)",
                required=False,
            ),
            ToolParameter(
                name="y", type="integer",
                description="Y coordinate (optional, uses current position if omitted)",
                required=False,
            ),
            ToolParameter(
                name="button", type="string",
                description="Mouse button: left, right, middle",
                required=False, default="left",
                enum=["left", "right", "middle"],
            ),
        ]

    @property
    def permission_level(self) -> PermissionLevel:
        return PermissionLevel.MEDIUM

    async def execute(self, **params: Any) -> ToolResult:
        try:
            import pyautogui
            pyautogui.FAILSAFE = True
            
            x = params.get("x")
            y = params.get("y")
            button = params.get("button", "left")
            
            if x is not None and y is not None:
                pyautogui.click(x, y, button=button)
                msg = f"Clicked {button} at ({x}, {y})"
            else:
                pyautogui.click(button=button)
                pos = pyautogui.position()
                msg = f"Clicked {button} at current position ({pos.x}, {pos.y})"
            
            logger.info(msg)
            return ToolResult.ok(message=msg)
        except Exception as e:
            return ToolResult.fail(str(e))


class MouseDoubleClickTool(Tool):
    @property
    def name(self) -> str:
        return "mouse.double_click"

    @property
    def description(self) -> str:
        return "Double-click the mouse at specified coordinates or current position."

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="x", type="integer",
                description="X coordinate (optional)",
                required=False,
            ),
            ToolParameter(
                name="y", type="integer",
                description="Y coordinate (optional)",
                required=False,
            ),
        ]

    @property
    def permission_level(self) -> PermissionLevel:
        return PermissionLevel.MEDIUM

    async def execute(self, **params: Any) -> ToolResult:
        try:
            import pyautogui
            pyautogui.FAILSAFE = True
            
            x = params.get("x")
            y = params.get("y")
            
            if x is not None and y is not None:
                pyautogui.doubleClick(x, y)
                msg = f"Double-clicked at ({x}, {y})"
            else:
                pyautogui.doubleClick()
                msg = "Double-clicked at current position"
            
            logger.info(msg)
            return ToolResult.ok(message=msg)
        except Exception as e:
            return ToolResult.fail(str(e))


def get_tools() -> list[Tool]:
    return [MouseMoveTool(), MouseClickTool(), MouseDoubleClickTool()]

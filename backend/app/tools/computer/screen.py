"""
NEXA Computer Tools — Screen capture and reading.
"""

from __future__ import annotations

import base64
import io
from pathlib import Path
from typing import Any

from loguru import logger

from app.security.permissions import PermissionLevel
from app.tools.base import Tool, ToolParameter, ToolResult


class ScreenCaptureTool(Tool):
    """Capture a screenshot of the entire screen or a region."""

    @property
    def name(self) -> str:
        return "screen.capture"

    @property
    def description(self) -> str:
        return (
            "Capture a screenshot of the screen. Can capture the full screen "
            "or a specific region. Returns the screenshot as a base64 image "
            "and saves to disk."
        )

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="region",
                type="object",
                description=(
                    "Optional screen region: {left, top, width, height}. "
                    "Omit for full screen."
                ),
                required=False,
            ),
            ToolParameter(
                name="save_path",
                type="string",
                description="Optional file path to save the screenshot.",
                required=False,
            ),
        ]

    @property
    def permission_level(self) -> PermissionLevel:
        return PermissionLevel.LOW

    async def execute(self, **params: Any) -> ToolResult:
        try:
            import mss
            from PIL import Image

            region = params.get("region")
            save_path = params.get("save_path")

            with mss.mss() as sct:
                if region:
                    monitor = {
                        "left": region.get("left", 0),
                        "top": region.get("top", 0),
                        "width": region.get("width", 1920),
                        "height": region.get("height", 1080),
                    }
                else:
                    monitor = sct.monitors[0]  # Full screen

                screenshot = sct.grab(monitor)
                img = Image.frombytes(
                    "RGB",
                    (screenshot.width, screenshot.height),
                    screenshot.rgb,
                )

            # Save to file if requested
            artifacts = []
            if save_path:
                path = Path(save_path)
                path.parent.mkdir(parents=True, exist_ok=True)
                img.save(str(path))
                artifacts.append(str(path))
            else:
                # Save to default location
                default_dir = Path.home() / ".nexa" / "screenshots"
                default_dir.mkdir(parents=True, exist_ok=True)
                from datetime import datetime
                filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                path = default_dir / filename
                img.save(str(path))
                artifacts.append(str(path))

            # Also create base64 for LLM
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

            logger.info(f"Screenshot captured: {path}")

            return ToolResult.ok(
                data={
                    "path": str(path),
                    "width": img.width,
                    "height": img.height,
                    "base64_length": len(b64),
                },
                message=f"Screenshot saved to {path}",
            )

        except Exception as e:
            logger.error(f"Screen capture failed: {e}")
            return ToolResult.fail(str(e))


class ScreenReadTool(Tool):
    """Read text content visible on the screen (OCR placeholder)."""

    @property
    def name(self) -> str:
        return "screen.read"

    @property
    def description(self) -> str:
        return (
            "Read and extract text content from the current screen. "
            "Captures a screenshot and describes what is visible."
        )

    @property
    def parameters(self) -> list[ToolParameter]:
        return []

    @property
    def permission_level(self) -> PermissionLevel:
        return PermissionLevel.LOW

    async def execute(self, **params: Any) -> ToolResult:
        try:
            import mss
            
            with mss.mss() as sct:
                monitor = sct.monitors[0]
                screenshot = sct.grab(monitor)
            
            # Return screen dimensions and basic info
            # Full OCR can be added with tesseract or cloud vision API
            return ToolResult.ok(
                data={
                    "width": screenshot.width,
                    "height": screenshot.height,
                    "description": (
                        f"Screen capture: {screenshot.width}x{screenshot.height}. "
                        "Full OCR not yet integrated — use screen.capture for visual analysis."
                    ),
                },
                message="Screen state captured",
            )

        except Exception as e:
            return ToolResult.fail(str(e))


def get_tools() -> list[Tool]:
    """Return all screen tools."""
    return [ScreenCaptureTool(), ScreenReadTool()]

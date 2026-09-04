"""
NEXA Tool System — Base classes for the universal tool architecture.

Every tool in NEXA inherits from the Tool base class and registers
itself with the ToolRegistry for discovery by the agent.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel

from app.security.permissions import PermissionLevel


class ToolCategory(str, Enum):
    COMPUTER = "computer"
    OS = "os"
    FILESYSTEM = "filesystem"
    BROWSER = "browser"
    APPLICATION = "app"
    CREATION = "creation"
    SERVICE = "service"
    ANDROID = "android"


class ToolParameter(BaseModel):
    """Description of a tool parameter."""
    name: str
    type: str  # "string", "integer", "boolean", "number", "array", "object"
    description: str
    required: bool = True
    default: Any = None
    enum: Optional[list[str]] = None


class ToolResult(BaseModel):
    """Result from executing a tool."""
    success: bool
    data: Any = None
    error: Optional[str] = None
    message: Optional[str] = None
    artifacts: list[str] = []  # paths to generated files, screenshots, etc.

    @classmethod
    def ok(cls, data: Any = None, message: str = "") -> "ToolResult":
        return cls(success=True, data=data, message=message)

    @classmethod
    def fail(cls, error: str, data: Any = None) -> "ToolResult":
        return cls(success=False, error=error, data=data)


class Tool(ABC):
    """
    Abstract base class for all NEXA tools.
    
    Every tool must define:
    - name: unique dotted name (e.g., 'filesystem.search')
    - description: what the tool does (used by LLM for selection)
    - parameters: list of ToolParameter objects
    - permission_level: LOW, MEDIUM, or HIGH
    - category: which category this tool belongs to
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique tool name in dotted notation (e.g., 'screen.capture')."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of what this tool does."""
        ...

    @property
    @abstractmethod
    def parameters(self) -> list[ToolParameter]:
        """List of parameters this tool accepts."""
        ...

    @property
    @abstractmethod
    def permission_level(self) -> PermissionLevel:
        """Risk level of this tool."""
        ...

    @property
    def category(self) -> ToolCategory:
        """Tool category, derived from name prefix."""
        prefix = self.name.split(".")[0]
        mapping = {
            "screen": ToolCategory.COMPUTER,
            "mouse": ToolCategory.COMPUTER,
            "keyboard": ToolCategory.COMPUTER,
            "clipboard": ToolCategory.COMPUTER,
            "os": ToolCategory.OS,
            "app": ToolCategory.APPLICATION,
            "filesystem": ToolCategory.FILESYSTEM,
            "browser": ToolCategory.BROWSER,
            "content": ToolCategory.CREATION,
            "image": ToolCategory.CREATION,
        }
        return mapping.get(prefix, ToolCategory.SERVICE)

    @abstractmethod
    async def execute(self, **params: Any) -> ToolResult:
        """Execute the tool with the given parameters."""
        ...

    async def verify(self, result: ToolResult) -> bool:
        """Verify the tool execution result. Override for custom verification."""
        return result.success

    def to_llm_schema(self) -> dict[str, Any]:
        """Convert to LLM function-calling format."""
        properties = {}
        required = []
        
        for param in self.parameters:
            prop: dict[str, Any] = {
                "type": param.type,
                "description": param.description,
            }
            if param.enum:
                prop["enum"] = param.enum
            if param.default is not None:
                prop["default"] = param.default
            properties[param.name] = prop
            if param.required:
                required.append(param.name)

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            },
        }

    def to_info(self) -> dict[str, Any]:
        """Convert to public info dict."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {p.name: p.model_dump() for p in self.parameters},
            "permission_level": self.permission_level.value,
            "category": self.category.value,
        }

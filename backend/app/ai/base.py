"""
NEXA AI Base — Abstract LLM provider interface.

All LLM providers (OpenAI, Gemini, Anthropic, Ollama) implement this
interface so the agent can swap providers without code changes.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class LLMMessage:
    """A message in LLM conversation format."""
    role: str  # "system", "user", "assistant", "tool"
    content: str
    tool_call_id: Optional[str] = None
    tool_calls: Optional[list[dict[str, Any]]] = None


@dataclass
class LLMToolCall:
    """A tool call returned by the LLM."""
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class LLMResponse:
    """Response from an LLM completion."""
    content: str = ""
    tool_calls: list[LLMToolCall] = field(default_factory=list)
    finish_reason: str = "stop"
    usage: dict[str, int] = field(default_factory=dict)
    raw: Any = None

    @property
    def has_tool_calls(self) -> bool:
        return len(self.tool_calls) > 0


class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.
    
    All providers must implement:
    - complete(): standard chat completion with optional tool support
    - complete_structured(): completion with structured JSON output
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name."""
        ...

    @property
    @abstractmethod
    def model(self) -> str:
        """Current model name."""
        ...

    @abstractmethod
    async def complete(
        self,
        messages: list[LLMMessage],
        tools: Optional[list[dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """
        Generate a completion.
        
        Args:
            messages: Conversation messages
            tools: Optional list of tool schemas for function calling
            temperature: Sampling temperature
            max_tokens: Maximum response tokens
            
        Returns:
            LLMResponse with content and/or tool calls
        """
        ...

    @abstractmethod
    async def complete_structured(
        self,
        messages: list[LLMMessage],
        response_schema: dict[str, Any],
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> dict[str, Any]:
        """
        Generate a structured JSON response matching the given schema.
        
        Args:
            messages: Conversation messages  
            response_schema: JSON schema the response must match
            temperature: Sampling temperature (lower for structured output)
            max_tokens: Maximum response tokens
            
        Returns:
            Parsed JSON dict matching the schema
        """
        ...

    async def health_check(self) -> bool:
        """Check if the provider is accessible."""
        try:
            response = await self.complete(
                messages=[LLMMessage(role="user", content="Say 'ok'")],
                max_tokens=10,
            )
            return bool(response.content)
        except Exception:
            return False

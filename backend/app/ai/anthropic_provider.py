"""
NEXA AI — Anthropic Claude Provider.
"""

from __future__ import annotations

import json
from typing import Any, Optional

from loguru import logger

from app.ai.base import LLMMessage, LLMProvider, LLMResponse, LLMToolCall


class AnthropicProvider(LLMProvider):
    """Anthropic Claude LLM provider."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        self._api_key = api_key
        self._model = model
        self._client = None
        self._init_client()

    def _init_client(self):
        try:
            import anthropic
            self._client = anthropic.AsyncAnthropic(api_key=self._api_key)
            logger.info(f"Anthropic provider initialized: {self._model}")
        except ImportError:
            logger.error("anthropic package not installed")
            raise

    @property
    def name(self) -> str:
        return "anthropic"

    @property
    def model(self) -> str:
        return self._model

    def _convert_messages(
        self, messages: list[LLMMessage]
    ) -> tuple[str, list[dict[str, Any]]]:
        """Convert to Anthropic format. Returns (system, messages)."""
        system = ""
        converted = []

        for msg in messages:
            if msg.role == "system":
                system = msg.content
            elif msg.role == "user":
                converted.append({
                    "role": "user",
                    "content": msg.content,
                })
            elif msg.role == "assistant":
                content_parts = []
                if msg.content:
                    content_parts.append({"type": "text", "text": msg.content})
                if msg.tool_calls:
                    for tc in msg.tool_calls:
                        args = tc.get("function", {}).get("arguments", "{}")
                        if isinstance(args, str):
                            args = json.loads(args)
                        content_parts.append({
                            "type": "tool_use",
                            "id": tc.get("id", ""),
                            "name": tc["function"]["name"],
                            "input": args,
                        })
                converted.append({
                    "role": "assistant",
                    "content": content_parts or msg.content,
                })
            elif msg.role == "tool":
                converted.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": msg.tool_call_id or "",
                        "content": msg.content,
                    }],
                })

        return system, converted

    def _convert_tools(self, tools: list[dict[str, Any]]) -> list[dict]:
        """Convert OpenAI-style tools to Anthropic format."""
        anthropic_tools = []
        for tool in tools:
            func = tool.get("function", {})
            anthropic_tools.append({
                "name": func.get("name", ""),
                "description": func.get("description", ""),
                "input_schema": func.get("parameters", {}),
            })
        return anthropic_tools

    async def complete(
        self,
        messages: list[LLMMessage],
        tools: Optional[list[dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        system, converted_messages = self._convert_messages(messages)

        kwargs: dict[str, Any] = {
            "model": self._model,
            "messages": converted_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if system:
            kwargs["system"] = system
        if tools:
            kwargs["tools"] = self._convert_tools(tools)

        try:
            response = await self._client.messages.create(**kwargs)

            content = ""
            tool_calls = []

            for block in response.content:
                if block.type == "text":
                    content += block.text
                elif block.type == "tool_use":
                    tool_calls.append(LLMToolCall(
                        id=block.id,
                        name=block.name,
                        arguments=block.input if isinstance(block.input, dict) else {},
                    ))

            usage = {
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": (
                    response.usage.input_tokens + response.usage.output_tokens
                ),
            }

            return LLMResponse(
                content=content,
                tool_calls=tool_calls,
                finish_reason="tool_calls" if tool_calls else response.stop_reason or "stop",
                usage=usage,
                raw=response,
            )

        except Exception as e:
            logger.error(f"Anthropic completion error: {e}")
            raise

    async def complete_structured(
        self,
        messages: list[LLMMessage],
        response_schema: dict[str, Any],
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> dict[str, Any]:
        schema_instruction = (
            f"\n\nRespond with ONLY valid JSON matching this schema:\n"
            f"```json\n{json.dumps(response_schema, indent=2)}\n```\n"
            f"Do not include any text outside the JSON."
        )

        modified_messages = list(messages)
        if modified_messages and modified_messages[-1].role == "user":
            modified_messages[-1] = LLMMessage(
                role="user",
                content=modified_messages[-1].content + schema_instruction,
            )
        else:
            modified_messages.append(
                LLMMessage(role="user", content=schema_instruction)
            )

        response = await self.complete(
            messages=modified_messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        content = response.content.strip()
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(lines[1:-1]) if len(lines) > 2 else content

        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse structured response: {e}")
            return {"error": str(e), "raw": content}

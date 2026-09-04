"""
NEXA AI — OpenAI Provider.
"""

from __future__ import annotations

import json
from typing import Any, Optional

from loguru import logger

from app.ai.base import LLMMessage, LLMProvider, LLMResponse, LLMToolCall


class OpenAIProvider(LLMProvider):
    """OpenAI GPT LLM provider."""

    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self._api_key = api_key
        self._model = model
        self._client = None
        self._init_client()

    def _init_client(self):
        try:
            import openai
            self._client = openai.AsyncOpenAI(api_key=self._api_key)
            logger.info(f"OpenAI provider initialized: {self._model}")
        except ImportError:
            logger.error("openai package not installed")
            raise

    @property
    def name(self) -> str:
        return "openai"

    @property
    def model(self) -> str:
        return self._model

    def _convert_messages(
        self, messages: list[LLMMessage]
    ) -> list[dict[str, Any]]:
        """Convert LLMMessages to OpenAI format."""
        result = []
        for msg in messages:
            entry: dict[str, Any] = {
                "role": msg.role,
                "content": msg.content,
            }
            if msg.tool_call_id:
                entry["tool_call_id"] = msg.tool_call_id
            if msg.tool_calls:
                entry["tool_calls"] = msg.tool_calls
            result.append(entry)
        return result

    async def complete(
        self,
        messages: list[LLMMessage],
        tools: Optional[list[dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        kwargs: dict[str, Any] = {
            "model": self._model,
            "messages": self._convert_messages(messages),
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        try:
            response = await self._client.chat.completions.create(**kwargs)
            choice = response.choices[0]
            message = choice.message

            content = message.content or ""
            tool_calls = []

            if message.tool_calls:
                for tc in message.tool_calls:
                    args = tc.function.arguments
                    if isinstance(args, str):
                        args = json.loads(args)
                    tool_calls.append(LLMToolCall(
                        id=tc.id,
                        name=tc.function.name,
                        arguments=args,
                    ))

            usage = {}
            if response.usage:
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }

            return LLMResponse(
                content=content,
                tool_calls=tool_calls,
                finish_reason=choice.finish_reason or "stop",
                usage=usage,
                raw=response,
            )

        except Exception as e:
            logger.error(f"OpenAI completion error: {e}")
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

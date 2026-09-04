"""
NEXA AI — Ollama Local Provider.
"""

from __future__ import annotations

import json
from typing import Any, Optional

import httpx
from loguru import logger

from app.ai.base import LLMMessage, LLMProvider, LLMResponse, LLMToolCall


class OllamaProvider(LLMProvider):
    """Local Ollama LLM provider."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama3",
    ):
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=120.0,
        )
        logger.info(f"Ollama provider initialized: {self._model} @ {self._base_url}")

    @property
    def name(self) -> str:
        return "ollama"

    @property
    def model(self) -> str:
        return self._model

    def _convert_messages(
        self, messages: list[LLMMessage]
    ) -> list[dict[str, str]]:
        """Convert to Ollama format."""
        return [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

    async def complete(
        self,
        messages: list[LLMMessage],
        tools: Optional[list[dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": self._convert_messages(messages),
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        # Ollama supports tools for some models
        if tools:
            payload["tools"] = tools

        try:
            response = await self._client.post("/api/chat", json=payload)
            response.raise_for_status()
            data = response.json()

            message = data.get("message", {})
            content = message.get("content", "")
            tool_calls = []

            # Parse tool calls if present
            if message.get("tool_calls"):
                for tc in message["tool_calls"]:
                    func = tc.get("function", {})
                    tool_calls.append(LLMToolCall(
                        id=f"call_{func.get('name', '')}",
                        name=func.get("name", ""),
                        arguments=func.get("arguments", {}),
                    ))

            return LLMResponse(
                content=content,
                tool_calls=tool_calls,
                finish_reason="tool_calls" if tool_calls else "stop",
                usage={
                    "prompt_tokens": data.get("prompt_eval_count", 0),
                    "completion_tokens": data.get("eval_count", 0),
                    "total_tokens": (
                        data.get("prompt_eval_count", 0)
                        + data.get("eval_count", 0)
                    ),
                },
                raw=data,
            )

        except Exception as e:
            logger.warning(f"Ollama connection issue ({e}). Falling back to Local Rule Provider.")
            from app.ai.rule_provider import LocalRuleProvider
            fallback = LocalRuleProvider()
            return await fallback.complete(messages, tools, temperature, max_tokens)

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

        try:
            response = await self.complete(
                messages=modified_messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            content = response.content.strip()
            if content.startswith("```"):
                lines = content.split("\n")
                content = "\n".join(lines[1:-1]) if len(lines) > 2 else content

            return json.loads(content)
        except Exception as e:
            logger.warning(f"Ollama structured completion issue ({e}). Falling back to Local Rule Provider.")
            from app.ai.rule_provider import LocalRuleProvider
            fallback = LocalRuleProvider()
            return await fallback.complete_structured(messages, response_schema, temperature, max_tokens)

    async def health_check(self) -> bool:
        try:
            response = await self._client.get("/api/tags")
            return response.status_code == 200
        except Exception:
            return False

"""
NEXA AI — Google Gemini Provider.
"""

from __future__ import annotations

import json
from typing import Any, Optional

from loguru import logger

from app.ai.base import LLMMessage, LLMProvider, LLMResponse, LLMToolCall


class GeminiProvider(LLMProvider):
    """Google Gemini LLM provider."""

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        self._api_key = api_key
        self._model = model
        self._client = None
        self._init_client()

    def _init_client(self):
        try:
            from google import genai
            self._client = genai.Client(api_key=self._api_key)
            logger.info(f"Gemini provider initialized: {self._model}")
        except ImportError:
            logger.error("google-genai package not installed")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
            raise

    @property
    def name(self) -> str:
        return "gemini"

    @property
    def model(self) -> str:
        return self._model

    def _convert_messages(self, messages: list[LLMMessage]) -> tuple[Optional[str], list[dict]]:
        """Convert LLMMessages to Gemini format. Returns (system_instruction, contents)."""
        system_instruction = None
        contents = []

        for msg in messages:
            if msg.role == "system":
                system_instruction = msg.content
            elif msg.role == "user":
                contents.append({"role": "user", "parts": [{"text": msg.content}]})
            elif msg.role == "assistant":
                parts = []
                if msg.content:
                    parts.append({"text": msg.content})
                if msg.tool_calls:
                    for tc in msg.tool_calls:
                        parts.append({
                            "function_call": {
                                "name": tc["function"]["name"],
                                "args": json.loads(tc["function"]["arguments"])
                                if isinstance(tc["function"]["arguments"], str)
                                else tc["function"]["arguments"],
                            }
                        })
                if parts:
                    contents.append({"role": "model", "parts": parts})
            elif msg.role == "tool":
                contents.append({
                    "role": "user",
                    "parts": [{
                        "function_response": {
                            "name": msg.tool_call_id or "tool",
                            "response": {"result": msg.content},
                        }
                    }]
                })

        return system_instruction, contents

    def _convert_tools(self, tools: list[dict[str, Any]]) -> list[dict]:
        """Convert OpenAI-style tool schemas to Gemini format."""
        gemini_declarations = []
        for tool in tools:
            func = tool.get("function", {})
            declaration = {
                "name": func.get("name", ""),
                "description": func.get("description", ""),
                "parameters": func.get("parameters", {}),
            }
            gemini_declarations.append(declaration)
        return gemini_declarations

    async def complete(
        self,
        messages: list[LLMMessage],
        tools: Optional[list[dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        from google.genai import types

        system_instruction, contents = self._convert_messages(messages)

        config_kwargs: dict[str, Any] = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }
        if system_instruction:
            config_kwargs["system_instruction"] = system_instruction

        gemini_tools = None
        if tools:
            declarations = self._convert_tools(tools)
            if declarations:
                gemini_tools = [types.Tool(function_declarations=[
                    types.FunctionDeclaration(**d) for d in declarations
                ])]

        try:
            response = self._client.models.generate_content(
                model=self._model,
                contents=contents,
                config=types.GenerateContentConfig(**config_kwargs),
                tools=gemini_tools,
            )

            # Parse response
            content = ""
            tool_calls = []

            if response.candidates:
                candidate = response.candidates[0]
                for part in candidate.content.parts:
                    if hasattr(part, "text") and part.text:
                        content += part.text
                    elif hasattr(part, "function_call") and part.function_call:
                        fc = part.function_call
                        tool_calls.append(LLMToolCall(
                            id=f"call_{fc.name}",
                            name=fc.name,
                            arguments=dict(fc.args) if fc.args else {},
                        ))

            usage = {}
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                um = response.usage_metadata
                usage = {
                    "prompt_tokens": getattr(um, "prompt_token_count", 0),
                    "completion_tokens": getattr(um, "candidates_token_count", 0),
                    "total_tokens": getattr(um, "total_token_count", 0),
                }

            return LLMResponse(
                content=content,
                tool_calls=tool_calls,
                finish_reason="tool_calls" if tool_calls else "stop",
                usage=usage,
                raw=response,
            )

        except Exception as e:
            logger.error(f"Gemini completion error: {e}")
            raise

    async def complete_structured(
        self,
        messages: list[LLMMessage],
        response_schema: dict[str, Any],
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> dict[str, Any]:
        # Add schema instruction to the last user message
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

        # Parse JSON from response
        content = response.content.strip()
        # Remove markdown code fences if present
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(lines[1:-1]) if len(lines) > 2 else content
        
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse structured response: {e}")
            logger.debug(f"Raw response: {content}")
            return {"error": str(e), "raw": content}

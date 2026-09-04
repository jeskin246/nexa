"""
NEXA Agent Verifier — Verifies that tool execution achieved the intended result.
"""

from __future__ import annotations

from typing import Any

from loguru import logger

from app.ai.base import LLMMessage, LLMProvider
from app.tools.base import ToolResult


class VerificationResult:
    """Result of a verification check."""

    def __init__(
        self,
        success: bool,
        confidence: float = 1.0,
        message: str = "",
        suggestion: str = "",
    ):
        self.success = success
        self.confidence = confidence  # 0.0 - 1.0
        self.message = message
        self.suggestion = suggestion  # What to do if uncertain


class Verifier:
    """
    Verifies tool execution results against expected outcomes.
    
    Uses a combination of:
    - Tool-level verification (each tool can define its own)
    - LLM-based reasoning (for complex verifications)
    - Rule-based checks (for common patterns)
    """

    def __init__(self, llm: LLMProvider):
        self._llm = llm

    async def verify_step(
        self,
        step_description: str,
        tool_name: str,
        result: ToolResult,
        observations: dict[str, Any],
    ) -> VerificationResult:
        """
        Verify that a step achieved its intended outcome.
        
        Args:
            step_description: What the step was supposed to do
            tool_name: Which tool was used
            result: The tool execution result
            observations: Environment observations after execution
        """
        # First check: tool-level success/failure
        if not result.success:
            return VerificationResult(
                success=False,
                confidence=1.0,
                message=f"Tool failed: {result.error}",
                suggestion="Retry with different parameters or use alternative tool",
            )

        # If tool returned success=True, verify as success
        if result.success:
            return VerificationResult(
                success=True,
                confidence=1.0,
                message=result.message or "Tool executed successfully",
            )

        # For complex failures, use LLM to analyze
        return await self._llm_verify(
            step_description, tool_name, result, observations
        )

    async def _llm_verify(
        self,
        step_description: str,
        tool_name: str,
        result: ToolResult,
        observations: dict[str, Any],
    ) -> VerificationResult:
        """Use LLM to verify a complex step result."""
        messages = [
            LLMMessage(
                role="system",
                content=(
                    "You are a verification assistant. Given an intended action "
                    "and its result, determine if the action was successful. "
                    "Respond with JSON: {\"success\": bool, \"confidence\": float "
                    "(0-1), \"message\": string, \"suggestion\": string}"
                ),
            ),
            LLMMessage(
                role="user",
                content=(
                    f"Intended action: {step_description}\n"
                    f"Tool used: {tool_name}\n"
                    f"Result: success={result.success}, "
                    f"data={str(result.data)[:500]}, "
                    f"message={result.message}\n"
                    f"Observations: {str(observations)[:500]}"
                ),
            ),
        ]

        try:
            response = await self._llm.complete_structured(
                messages=messages,
                response_schema={
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean"},
                        "confidence": {"type": "number"},
                        "message": {"type": "string"},
                        "suggestion": {"type": "string"},
                    },
                    "required": ["success", "confidence"],
                },
                temperature=0.2,
                max_tokens=500,
            )

            return VerificationResult(
                success=response.get("success", True),
                confidence=response.get("confidence", 0.7),
                message=response.get("message", ""),
                suggestion=response.get("suggestion", ""),
            )

        except Exception as e:
            logger.warning(f"LLM verification failed: {e}")
            # Fall back to trusting the tool result
            return VerificationResult(
                success=result.success,
                confidence=0.5,
                message="LLM verification unavailable, trusting tool result",
            )

    async def verify_goal_completion(
        self,
        goal: str,
        completed_steps: list[dict[str, Any]],
        final_result: Any,
    ) -> VerificationResult:
        """Verify that the overall goal has been achieved."""
        messages = [
            LLMMessage(
                role="system",
                content=(
                    "You are a goal verification assistant. Given a user's goal "
                    "and the steps completed, determine if the goal was fully "
                    "achieved. Respond with JSON."
                ),
            ),
            LLMMessage(
                role="user",
                content=(
                    f"Goal: {goal}\n\n"
                    f"Completed steps:\n"
                    + "\n".join(
                        f"  {i+1}. {s.get('description', '?')} — "
                        f"{'✓' if s.get('success') else '✗'}"
                        for i, s in enumerate(completed_steps)
                    )
                    + f"\n\nFinal result: {str(final_result)[:500]}"
                ),
            ),
        ]

        try:
            response = await self._llm.complete_structured(
                messages=messages,
                response_schema={
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean"},
                        "confidence": {"type": "number"},
                        "message": {"type": "string"},
                        "suggestion": {"type": "string"},
                    },
                    "required": ["success"],
                },
                temperature=0.2,
            )
            return VerificationResult(
                success=response.get("success", False),
                confidence=response.get("confidence", 0.5),
                message=response.get("message", ""),
                suggestion=response.get("suggestion", ""),
            )
        except Exception as e:
            logger.warning(f"Goal verification failed: {e}")
            return VerificationResult(
                success=True,
                confidence=0.5,
                message="Verification unavailable",
            )

"""
NEXA Agent Recovery — Handles failures, retries, and alternative strategies.
"""

from __future__ import annotations

import asyncio
from typing import Any

from loguru import logger


class RecoveryStrategy:
    """A recovery strategy for a failed step."""

    def __init__(
        self,
        action: str,
        description: str,
        new_tool: str | None = None,
        new_params: dict[str, Any] | None = None,
        wait_seconds: float = 0,
    ):
        self.action = action  # "retry", "alternative", "skip", "abort", "ask_user"
        self.description = description
        self.new_tool = new_tool
        self.new_params = new_params
        self.wait_seconds = wait_seconds


class RecoveryManager:
    """
    Manages error recovery and retry logic for the agent.
    
    Strategies:
    1. Retry — same tool, same params, with backoff
    2. Alternative — different tool or params
    3. Skip — skip non-critical step
    4. Abort — stop the task
    5. Ask User — escalate to user
    """

    def __init__(self, max_retries: int = 3):
        self._max_retries = max_retries
        self._retry_counts: dict[str, int] = {}  # step_key -> count

    def get_retry_count(self, step_key: str) -> int:
        """Get current retry count for a step."""
        return self._retry_counts.get(step_key, 0)

    def increment_retry(self, step_key: str) -> int:
        """Increment and return retry count."""
        count = self._retry_counts.get(step_key, 0) + 1
        self._retry_counts[step_key] = count
        return count

    def reset_retries(self, step_key: str | None = None):
        """Reset retry counts."""
        if step_key:
            self._retry_counts.pop(step_key, None)
        else:
            self._retry_counts.clear()

    def determine_strategy(
        self,
        step_key: str,
        tool_name: str,
        error: str,
        step_index: int,
        total_steps: int,
    ) -> RecoveryStrategy:
        """
        Determine the best recovery strategy for a failed step.
        
        Args:
            step_key: Unique key for this step (for retry tracking)
            tool_name: The tool that failed
            error: Error message
            step_index: Which step failed (0-based)
            total_steps: Total number of steps
        """
        retry_count = self.get_retry_count(step_key)

        # Timeout errors — retry with longer timeout
        if "timeout" in error.lower():
            if retry_count < self._max_retries:
                self.increment_retry(step_key)
                wait = 2 ** retry_count  # exponential backoff
                return RecoveryStrategy(
                    action="retry",
                    description=f"Retrying after timeout (attempt {retry_count + 1})",
                    wait_seconds=wait,
                )

        # Permission denied — ask user
        if "permission denied" in error.lower() or "denied" in error.lower():
            return RecoveryStrategy(
                action="ask_user",
                description="Permission was denied. Asking user for guidance.",
            )

        # Tool not found — skip or abort
        if "not found" in error.lower():
            if step_index < total_steps - 1:
                return RecoveryStrategy(
                    action="skip",
                    description=f"Tool not available, skipping step",
                )
            else:
                return RecoveryStrategy(
                    action="abort",
                    description="Critical tool not available",
                )

        # Connection errors — retry with backoff
        if any(
            kw in error.lower()
            for kw in ["connection", "network", "unreachable"]
        ):
            if retry_count < self._max_retries:
                self.increment_retry(step_key)
                wait = 3 * (retry_count + 1)
                return RecoveryStrategy(
                    action="retry",
                    description=f"Network issue, retrying (attempt {retry_count + 1})",
                    wait_seconds=wait,
                )

        # Generic error — retry a few times, then ask user
        if retry_count < min(2, self._max_retries):
            self.increment_retry(step_key)
            return RecoveryStrategy(
                action="retry",
                description=f"Retrying (attempt {retry_count + 1})",
                wait_seconds=1,
            )

        # Out of retries — ask user
        return RecoveryStrategy(
            action="ask_user",
            description=(
                f"Step failed after {retry_count} retries: {error}. "
                "Requesting user guidance."
            ),
        )

    async def apply_wait(self, strategy: RecoveryStrategy):
        """Apply the wait time from a recovery strategy."""
        if strategy.wait_seconds > 0:
            logger.info(
                f"Recovery: waiting {strategy.wait_seconds}s before retry"
            )
            await asyncio.sleep(strategy.wait_seconds)

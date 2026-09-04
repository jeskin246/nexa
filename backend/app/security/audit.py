"""
NEXA Audit Logger — Records all tool executions and agent actions.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from loguru import logger


class AuditEntry:
    """A single audit log entry."""

    def __init__(
        self,
        action: str,
        tool_name: str,
        parameters: dict[str, Any],
        result: Optional[str] = None,
        success: bool = True,
        user_approved: Optional[bool] = None,
        task_id: Optional[str] = None,
        error: Optional[str] = None,
    ):
        self.timestamp = datetime.now().isoformat()
        self.action = action
        self.tool_name = tool_name
        self.parameters = parameters
        self.result = result
        self.success = success
        self.user_approved = user_approved
        self.task_id = task_id
        self.error = error

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "action": self.action,
            "tool_name": self.tool_name,
            "parameters": self.parameters,
            "result": self.result,
            "success": self.success,
            "user_approved": self.user_approved,
            "task_id": self.task_id,
            "error": self.error,
        }


class AuditLogger:
    """Persistent audit logger for all NEXA actions."""

    def __init__(self, log_path: Path):
        self._log_path = log_path
        self._log_path.parent.mkdir(parents=True, exist_ok=True)
        self._entries: list[AuditEntry] = []
        logger.info(f"Audit logger initialized: {self._log_path}")

    def log(
        self,
        action: str,
        tool_name: str,
        parameters: dict[str, Any] | None = None,
        result: str | None = None,
        success: bool = True,
        user_approved: bool | None = None,
        task_id: str | None = None,
        error: str | None = None,
    ):
        """Log an action to the audit trail."""
        entry = AuditEntry(
            action=action,
            tool_name=tool_name,
            parameters=parameters or {},
            result=result,
            success=success,
            user_approved=user_approved,
            task_id=task_id,
            error=error,
        )
        self._entries.append(entry)

        # Append to file
        try:
            with open(self._log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry.to_dict()) + "\n")
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")

    def get_recent(self, count: int = 50) -> list[dict[str, Any]]:
        """Get recent audit entries."""
        return [e.to_dict() for e in self._entries[-count:]]

    def get_by_task(self, task_id: str) -> list[dict[str, Any]]:
        """Get all audit entries for a specific task."""
        return [
            e.to_dict() for e in self._entries if e.task_id == task_id
        ]

    def clear(self):
        """Clear in-memory entries (file is preserved)."""
        self._entries.clear()
        logger.info("Audit log memory cleared")

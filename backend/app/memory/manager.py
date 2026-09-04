"""
NEXA Memory Manager — Short-term context, task memory, and user preferences.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from loguru import logger


class MemoryManager:
    """
    Manages NEXA's memory:
    - Short-term context: conversation history per session
    - Task memory: active and completed tasks
    - User preferences: persisted to JSON
    
    Does NOT store passwords, tokens, or sensitive credentials.
    """

    def __init__(self, memory_path: Path):
        self._memory_path = memory_path
        self._memory_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Short-term (session) context
        self._conversation_history: list[dict[str, str]] = []
        self._max_history = 50  # Keep last N messages
        
        # Task memory
        self._active_tasks: dict[str, dict[str, Any]] = {}
        self._completed_tasks: list[dict[str, Any]] = []
        
        # User preferences (persistent)
        self._preferences: dict[str, Any] = {}
        self._load_preferences()
        
        logger.info(f"Memory manager initialized: {self._memory_path}")

    # ─── Conversation History ───────────────────────────────────────────

    def add_message(self, role: str, content: str):
        """Add a message to conversation history."""
        self._conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        })
        # Trim to max history
        if len(self._conversation_history) > self._max_history:
            self._conversation_history = self._conversation_history[
                -self._max_history:
            ]

    def get_conversation_history(
        self, limit: int | None = None
    ) -> list[dict[str, str]]:
        """Get recent conversation history."""
        if limit:
            return self._conversation_history[-limit:]
        return list(self._conversation_history)

    def get_context_messages(self) -> list[dict[str, str]]:
        """Get conversation history formatted for LLM context."""
        return [
            {"role": msg["role"], "content": msg["content"]}
            for msg in self._conversation_history
        ]

    def clear_conversation(self):
        """Clear conversation history."""
        self._conversation_history.clear()
        logger.info("Conversation history cleared")

    # ─── Task Memory ───────────────────────────────────────────────────

    def store_task(self, task_id: str, task_data: dict[str, Any]):
        """Store an active task."""
        self._active_tasks[task_id] = {
            **task_data,
            "stored_at": datetime.now().isoformat(),
        }

    def get_task(self, task_id: str) -> Optional[dict[str, Any]]:
        """Get an active task."""
        return self._active_tasks.get(task_id)

    def complete_task(self, task_id: str, result: Any = None):
        """Mark a task as completed and archive it."""
        task = self._active_tasks.pop(task_id, None)
        if task:
            task["completed_at"] = datetime.now().isoformat()
            task["result"] = result
            self._completed_tasks.append(task)
            # Keep last 100 completed tasks
            if len(self._completed_tasks) > 100:
                self._completed_tasks = self._completed_tasks[-100:]

    def get_active_tasks(self) -> dict[str, dict[str, Any]]:
        """Get all active tasks."""
        return dict(self._active_tasks)

    # ─── User Preferences ──────────────────────────────────────────────

    def set_preference(self, key: str, value: Any):
        """Set a user preference (persisted)."""
        self._preferences[key] = value
        self._save_preferences()
        logger.debug(f"Preference set: {key}")

    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get a user preference."""
        return self._preferences.get(key, default)

    def get_all_preferences(self) -> dict[str, Any]:
        """Get all user preferences."""
        return dict(self._preferences)

    def delete_preference(self, key: str):
        """Delete a user preference."""
        self._preferences.pop(key, None)
        self._save_preferences()

    def clear_preferences(self):
        """Clear all user preferences."""
        self._preferences.clear()
        self._save_preferences()
        logger.info("User preferences cleared")

    def _load_preferences(self):
        """Load preferences from disk."""
        if self._memory_path.exists():
            try:
                with open(self._memory_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._preferences = data.get("preferences", {})
                logger.info(
                    f"Loaded {len(self._preferences)} preferences"
                )
            except Exception as e:
                logger.error(f"Failed to load preferences: {e}")
                self._preferences = {}

    def _save_preferences(self):
        """Save preferences to disk."""
        try:
            data = {
                "preferences": self._preferences,
                "updated_at": datetime.now().isoformat(),
            }
            with open(self._memory_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save preferences: {e}")

    # ─── Memory Summary for LLM ────────────────────────────────────────

    def get_context_summary(self) -> str:
        """Get a summary of memory context for the LLM."""
        parts = []
        
        # User preferences
        if self._preferences:
            prefs = ", ".join(
                f"{k}: {v}" for k, v in self._preferences.items()
            )
            parts.append(f"User preferences: {prefs}")
        
        # Active tasks
        if self._active_tasks:
            active = ", ".join(
                f"'{t.get('goal', 'unknown')}'"
                for t in self._active_tasks.values()
            )
            parts.append(f"Active tasks: {active}")
        
        return ". ".join(parts) if parts else ""

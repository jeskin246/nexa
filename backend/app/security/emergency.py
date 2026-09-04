"""
NEXA Emergency Stop — Immediately cancels all running agent tasks.
"""

from __future__ import annotations

import asyncio
from typing import Optional

from loguru import logger


class EmergencyStop:
    """Global emergency stop mechanism for all agent operations."""

    def __init__(self):
        self._stopped = False
        self._active_tasks: dict[str, asyncio.Task] = {}
        self._cancel_events: dict[str, asyncio.Event] = {}
        logger.info("Emergency stop system initialized")

    @property
    def is_stopped(self) -> bool:
        return self._stopped

    def register_task(self, task_id: str, task: asyncio.Task):
        """Register an active task that can be stopped."""
        self._active_tasks[task_id] = task
        self._cancel_events[task_id] = asyncio.Event()
        logger.debug(f"Registered task for emergency stop: {task_id}")

    def unregister_task(self, task_id: str):
        """Unregister a completed task."""
        self._active_tasks.pop(task_id, None)
        self._cancel_events.pop(task_id, None)
        logger.debug(f"Unregistered task: {task_id}")

    def get_cancel_event(self, task_id: str) -> Optional[asyncio.Event]:
        """Get the cancellation event for a task."""
        return self._cancel_events.get(task_id)

    def is_task_cancelled(self, task_id: str) -> bool:
        """Check if a specific task has been cancelled."""
        event = self._cancel_events.get(task_id)
        if event:
            return event.is_set()
        return self._stopped

    async def stop_task(self, task_id: str):
        """Stop a specific task."""
        logger.warning(f"Stopping task: {task_id}")
        
        # Set cancellation event
        event = self._cancel_events.get(task_id)
        if event:
            event.set()
        
        # Cancel the asyncio task
        task = self._active_tasks.get(task_id)
        if task and not task.done():
            task.cancel()
            try:
                await asyncio.wait_for(asyncio.shield(task), timeout=5.0)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                pass
        
        self.unregister_task(task_id)
        logger.info(f"Task stopped: {task_id}")

    async def stop_all(self):
        """Emergency stop — cancel ALL active tasks immediately."""
        logger.critical("EMERGENCY STOP ACTIVATED — Cancelling all tasks")
        self._stopped = True
        
        # Set all cancellation events
        for event in self._cancel_events.values():
            event.set()
        
        # Cancel all asyncio tasks
        tasks_to_cancel = list(self._active_tasks.items())
        for task_id, task in tasks_to_cancel:
            if not task.done():
                task.cancel()
        
        # Wait briefly for tasks to finish
        if tasks_to_cancel:
            await asyncio.gather(
                *[t for _, t in tasks_to_cancel],
                return_exceptions=True
            )
        
        self._active_tasks.clear()
        self._cancel_events.clear()
        logger.info("All tasks stopped")

    def reset(self):
        """Reset emergency stop state (after user acknowledges)."""
        self._stopped = False
        logger.info("Emergency stop reset")

    @property
    def active_task_ids(self) -> list[str]:
        """List all active task IDs."""
        return list(self._active_tasks.keys())

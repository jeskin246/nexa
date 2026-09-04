"""
NEXA Permission Manager — Controls tool access based on risk levels.
"""

from __future__ import annotations

import asyncio
from enum import Enum
from typing import Any, Callable, Optional, Awaitable

from loguru import logger


class PermissionLevel(str, Enum):
    LOW = "low"        # Auto-approve: search, read, analyze, screenshot
    MEDIUM = "medium"  # Configurable: create files, modify, install
    HIGH = "high"      # Always confirm: delete, send, publish, destructive


class PermissionDecision(str, Enum):
    APPROVED = "approved"
    DENIED = "denied"
    PENDING = "pending"


class PermissionPolicy(str, Enum):
    AUTO = "auto"
    ASK = "ask"
    BLOCKED = "blocked"


# Default policies per tool category
DEFAULT_POLICIES: dict[str, dict[PermissionLevel, PermissionPolicy]] = {
    "default": {
        PermissionLevel.LOW: PermissionPolicy.AUTO,
        PermissionLevel.MEDIUM: PermissionPolicy.ASK,
        PermissionLevel.HIGH: PermissionPolicy.ASK,
    }
}


class PermissionManager:
    """Manages tool execution permissions based on risk levels."""

    def __init__(self, medium_risk_policy: str = "ask"):
        self._policies: dict[str, dict[PermissionLevel, PermissionPolicy]] = {
            **DEFAULT_POLICIES
        }
        # Override medium risk policy from config
        default_medium = PermissionPolicy(medium_risk_policy)
        self._policies["default"][PermissionLevel.MEDIUM] = default_medium
        
        # Callback to request user confirmation (set by websocket handler)
        self._confirmation_callback: Optional[
            Callable[[str, str, str, dict], Awaitable[bool]]
        ] = None
        
        # Pending confirmations
        self._pending: dict[str, asyncio.Event] = {}
        self._decisions: dict[str, bool] = {}
    
    def set_confirmation_callback(
        self,
        callback: Callable[[str, str, str, dict], Awaitable[bool]]
    ):
        """Set the callback used to request user confirmation via WebSocket."""
        self._confirmation_callback = callback
    
    def get_policy(
        self, tool_name: str, permission_level: PermissionLevel
    ) -> PermissionPolicy:
        """Get the policy for a tool at a given permission level."""
        category = tool_name.split(".")[0] if "." in tool_name else "default"
        policies = self._policies.get(category, self._policies["default"])
        return policies.get(permission_level, PermissionPolicy.ASK)
    
    def update_policy(
        self,
        category: str,
        level: PermissionLevel,
        policy: PermissionPolicy
    ):
        """Update permission policy for a category."""
        if category not in self._policies:
            self._policies[category] = dict(DEFAULT_POLICIES["default"])
        self._policies[category][level] = policy
        logger.info(f"Updated policy: {category}/{level.value} → {policy.value}")
    
    async def check_permission(
        self,
        task_id: str,
        tool_name: str,
        permission_level: PermissionLevel,
        parameters: dict[str, Any],
        description: str = "",
    ) -> PermissionDecision:
        """
        Check if a tool execution is permitted.
        Returns APPROVED, DENIED, or requests user confirmation.
        """
        policy = self.get_policy(tool_name, permission_level)
        
        if policy == PermissionPolicy.AUTO:
            logger.debug(f"Auto-approved: {tool_name}")
            return PermissionDecision.APPROVED
        
        if policy == PermissionPolicy.BLOCKED:
            logger.warning(f"Blocked by policy: {tool_name}")
            return PermissionDecision.DENIED
        
        # ASK policy — request user confirmation
        if self._confirmation_callback is None:
            logger.warning(
                f"No confirmation callback set, auto-approving: {tool_name}"
            )
            return PermissionDecision.APPROVED
        
        logger.info(f"Requesting confirmation for: {tool_name}")
        
        try:
            approved = await self._confirmation_callback(
                task_id, tool_name, description, parameters
            )
            decision = (
                PermissionDecision.APPROVED if approved
                else PermissionDecision.DENIED
            )
            logger.info(f"User decision for {tool_name}: {decision.value}")
            return decision
        except asyncio.TimeoutError:
            logger.warning(f"Confirmation timeout for: {tool_name}")
            return PermissionDecision.DENIED
        except Exception as e:
            logger.error(f"Confirmation error for {tool_name}: {e}")
            return PermissionDecision.DENIED
    
    def resolve_confirmation(self, task_id: str, approved: bool):
        """Resolve a pending confirmation request."""
        if task_id in self._pending:
            self._decisions[task_id] = approved
            self._pending[task_id].set()

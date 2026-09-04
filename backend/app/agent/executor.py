"""
NEXA Agent Executor — Executes tools with permission checks and error handling.
"""

from __future__ import annotations

import asyncio
from typing import Any, Optional

from loguru import logger

from app.security.audit import AuditLogger
from app.security.permissions import PermissionDecision, PermissionManager
from app.tools.base import Tool, ToolResult
from app.tools.registry import ToolRegistry


class Executor:
    """
    Executes tools with:
    - Permission checking before execution
    - Timeout management
    - Error handling and reporting
    - Audit logging
    """

    def __init__(
        self,
        registry: ToolRegistry,
        permission_manager: PermissionManager,
        audit_logger: AuditLogger,
        default_timeout: float = 60.0,
    ):
        self._registry = registry
        self._permissions = permission_manager
        self._audit = audit_logger
        self._default_timeout = default_timeout

    async def execute(
        self,
        task_id: str,
        tool_name: str,
        parameters: dict[str, Any],
        timeout: float | None = None,
    ) -> ToolResult:
        """
        Execute a tool by name with the given parameters.
        
        1. Look up tool in registry
        2. Check permissions
        3. Execute with timeout
        4. Log to audit trail
        5. Return result
        """
        tool = self._registry.get(tool_name)
        if not tool:
            error_msg = f"Tool not found: {tool_name}"
            logger.error(error_msg)
            self._audit.log(
                action="execute",
                tool_name=tool_name,
                parameters=parameters,
                success=False,
                error=error_msg,
                task_id=task_id,
            )
            return ToolResult.fail(error_msg)

        # Check permissions
        description = (
            f"Execute {tool_name} with parameters: "
            f"{self._sanitize_params(parameters)}"
        )
        
        decision = await self._permissions.check_permission(
            task_id=task_id,
            tool_name=tool_name,
            permission_level=tool.permission_level,
            parameters=parameters,
            description=description,
        )

        if decision == PermissionDecision.DENIED:
            msg = f"Permission denied for tool: {tool_name}"
            logger.warning(msg)
            self._audit.log(
                action="execute",
                tool_name=tool_name,
                parameters=parameters,
                success=False,
                error=msg,
                user_approved=False,
                task_id=task_id,
            )
            return ToolResult.fail(msg)

        if decision == PermissionDecision.PENDING:
            msg = f"Waiting for user confirmation: {tool_name}"
            logger.info(msg)
            return ToolResult.fail(msg)

        # Execute with timeout
        exec_timeout = timeout or self._default_timeout
        
        try:
            logger.info(
                f"Executing tool: {tool_name} "
                f"(timeout: {exec_timeout}s)"
            )
            
            result = await asyncio.wait_for(
                tool.execute(**parameters),
                timeout=exec_timeout,
            )

            # Audit log
            self._audit.log(
                action="execute",
                tool_name=tool_name,
                parameters=parameters,
                result=str(result.data)[:500] if result.data else None,
                success=result.success,
                error=result.error,
                user_approved=True,
                task_id=task_id,
            )

            if result.success:
                logger.info(f"Tool succeeded: {tool_name}")
            else:
                logger.warning(
                    f"Tool returned failure: {tool_name} — {result.error}"
                )

            return result

        except asyncio.TimeoutError:
            error_msg = f"Tool execution timed out after {exec_timeout}s: {tool_name}"
            logger.error(error_msg)
            self._audit.log(
                action="execute",
                tool_name=tool_name,
                parameters=parameters,
                success=False,
                error=error_msg,
                task_id=task_id,
            )
            return ToolResult.fail(error_msg)

        except Exception as e:
            error_msg = f"Tool execution error: {tool_name} — {str(e)}"
            logger.error(error_msg)
            self._audit.log(
                action="execute",
                tool_name=tool_name,
                parameters=parameters,
                success=False,
                error=error_msg,
                task_id=task_id,
            )
            return ToolResult.fail(error_msg)

    def _sanitize_params(self, params: dict[str, Any]) -> str:
        """Sanitize parameters for display (remove sensitive data)."""
        safe = {}
        sensitive_keys = {"password", "token", "secret", "key", "credential"}
        for k, v in params.items():
            if any(s in k.lower() for s in sensitive_keys):
                safe[k] = "***"
            elif isinstance(v, str) and len(v) > 200:
                safe[k] = v[:200] + "..."
            else:
                safe[k] = v
        return str(safe)

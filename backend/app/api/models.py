"""
NEXA API Models — Pydantic models for WebSocket and REST communication.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# ─── Agent States ───────────────────────────────────────────────────────────────

class AgentState(str, Enum):
    IDLE = "idle"
    LISTENING = "listening"
    THINKING = "thinking"
    PLANNING = "planning"
    EXECUTING = "executing"
    OBSERVING = "observing"
    WAITING = "waiting"
    SUCCESS = "success"
    ERROR = "error"


class StepStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


# ─── Task Models ────────────────────────────────────────────────────────────────

class TaskStep(BaseModel):
    """A single step in a task plan."""
    index: int
    description: str
    tool_name: Optional[str] = None
    status: StepStatus = StepStatus.PENDING
    result: Optional[str] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class TaskPlan(BaseModel):
    """A plan created by the agent for a user goal."""
    task_id: str
    goal: str
    steps: list[TaskStep] = []
    created_at: datetime = Field(default_factory=datetime.now)
    status: str = "created"


class TaskProgress(BaseModel):
    """Progress update for a running task."""
    task_id: str
    current_step: int
    total_steps: int
    percentage: float
    status: str
    message: str


# ─── WebSocket Messages ────────────────────────────────────────────────────────

class WSMessageType(str, Enum):
    # Client → Server
    GOAL = "goal"
    CONFIRM = "confirm"
    DENY = "deny"
    STOP = "stop"
    SYSTEM_INFO = "system_info"
    PING = "ping"

    # Server → Client
    STATUS = "status"
    PLAN = "plan"
    STEP_UPDATE = "step_update"
    CONFIRM_REQUEST = "confirm_request"
    RESULT = "result"
    ERROR = "error"
    SYSTEM_DATA = "system_data"
    PONG = "pong"
    TASK_COMPLETE = "task_complete"


class WSMessage(BaseModel):
    """Base WebSocket message."""
    type: WSMessageType
    task_id: Optional[str] = None
    data: Optional[dict[str, Any]] = None
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class WSGoalMessage(BaseModel):
    """Client sends a goal."""
    type: str = "goal"
    content: str


class WSConfirmMessage(BaseModel):
    """Client confirms or denies a permission request."""
    type: str  # "confirm" or "deny"
    task_id: str


class WSStopMessage(BaseModel):
    """Client requests emergency stop."""
    type: str = "stop"
    task_id: Optional[str] = None


# ─── Confirmation Request ──────────────────────────────────────────────────────

class ConfirmationRequest(BaseModel):
    """A permission request sent to the user."""
    task_id: str
    action: str
    tool_name: str
    parameters: dict[str, Any] = {}
    risk_level: str
    description: str


# ─── System Info ────────────────────────────────────────────────────────────────

class SystemInfo(BaseModel):
    """System telemetry data."""
    cpu_percent: float = 0.0
    memory_total: int = 0
    memory_used: int = 0
    memory_percent: float = 0.0
    disk_total: int = 0
    disk_used: int = 0
    disk_percent: float = 0.0
    network_sent: int = 0
    network_recv: int = 0
    battery_percent: Optional[float] = None
    battery_charging: Optional[bool] = None
    boot_time: Optional[datetime] = None
    active_window: Optional[str] = None
    process_count: int = 0


# ─── Tool Info ──────────────────────────────────────────────────────────────────

class ToolInfo(BaseModel):
    """Public info about a registered tool."""
    name: str
    description: str
    parameters: dict[str, Any]
    permission_level: str
    category: str = "general"


class ToolResult(BaseModel):
    """Result from a tool execution."""
    success: bool
    data: Any = None
    error: Optional[str] = None
    message: Optional[str] = None
    artifacts: list[str] = []  # file paths, screenshots, etc.

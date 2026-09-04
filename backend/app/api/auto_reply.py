"""
NEXA — Auto-Reply REST Endpoints.
Provides configuration, activity logs, and emergency stop for auto-reply.
"""

from typing import Dict, Any, List
from fastapi import APIRouter

router = APIRouter(prefix="/api/auto-reply", tags=["auto-reply"])

# In-memory store
_auto_reply_config: Dict[str, Any] = {
    "enabled": False,
    "user_status": "AVAILABLE",
    "waiting_time_seconds": 30,
    "cooldown_minutes": 5,
    "username": "User",
    "message_template": "Hey, I am currently unavailable.",
    "enabled_apps": {"WhatsApp": True, "Instagram": False},
}

_auto_reply_logs: List[Dict[str, Any]] = []


@router.get("/config")
async def get_auto_reply_config():
    """Fetch current auto-reply configuration."""
    return _auto_reply_config


@router.post("/config")
async def update_auto_reply_config(payload: Dict[str, Any]):
    """Update auto-reply configuration."""
    _auto_reply_config.update(payload)
    return _auto_reply_config


@router.get("/logs")
async def get_auto_reply_logs():
    """Fetch auto-reply activity logs."""
    return _auto_reply_logs


@router.post("/logs")
async def add_auto_reply_log(log_entry: Dict[str, Any]):
    """Record an auto-reply activity log."""
    _auto_reply_logs.append(log_entry)
    return {"status": "ok", "log": log_entry}


@router.post("/stop-all")
async def emergency_stop_auto_reply():
    """Emergency stop: disables auto-reply immediately."""
    _auto_reply_config["enabled"] = False
    return {
        "status": "stopped",
        "config": _auto_reply_config,
    }

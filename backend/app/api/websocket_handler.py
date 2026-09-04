
"""
NEXA WebSocket Handler — Manages real-time communication with the Flutter frontend.
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from typing import Any, Optional

from fastapi import WebSocket, WebSocketDisconnect
from loguru import logger

from app.agent.loop import AgentLoop
from app.api.models import AgentState
from app.security.emergency import EmergencyStop


class ConnectionManager:
    """Manages active WebSocket connections."""

    def __init__(self):
        self._connections: list[WebSocket] = []
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        async with self._lock:
            self._connections.append(websocket)
        logger.info(f"Client connected. Total: {len(self._connections)}")

    async def disconnect(self, websocket: WebSocket):
        async with self._lock:
            if websocket in self._connections:
                self._connections.remove(websocket)
        logger.info(f"Client disconnected. Total: {len(self._connections)}")

    async def broadcast(self, message: dict[str, Any]):
        """Send a message to all connected clients."""
        disconnected = []
        async with self._lock:
            for ws in self._connections:
                try:
                    await ws.send_json(message)
                except Exception:
                    disconnected.append(ws)
            for ws in disconnected:
                self._connections.remove(ws)

    async def send_to(self, websocket: WebSocket, message: dict[str, Any]):
        """Send a message to a specific client."""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send message: {e}")


class WebSocketHandler:
    """
    Handles WebSocket communication between frontend and agent.
    
    Protocol:
    - Client sends: goal, confirm, deny, stop, system_info, ping
    - Server sends: status, plan, step_update, confirm_request, 
                    result, error, system_data, pong, task_complete
    """

    def __init__(
        self,
        agent_loop: AgentLoop,
        emergency_stop: EmergencyStop,
        connection_manager: ConnectionManager,
    ):
        self._agent = agent_loop
        self._emergency_stop = emergency_stop
        self._connections = connection_manager
        self._pending_confirmations: dict[str, asyncio.Future] = {}

    async def handle_connection(self, websocket: WebSocket):
        """Handle a new WebSocket connection."""
        await self._connections.connect(websocket)

        # Send initial state
        await self._connections.send_to(websocket, {
            "type": "status",
            "state": AgentState.IDLE.value,
            "message": "NEXA is ready. What can I accomplish for you?",
            "timestamp": datetime.now().isoformat(),
        })

        try:
            while True:
                data = await websocket.receive_text()
                await self._process_message(websocket, data)
        except WebSocketDisconnect:
            logger.info("WebSocket client disconnected")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            await self._connections.disconnect(websocket)

    async def _process_message(self, websocket: WebSocket, raw: str):
        """Process an incoming WebSocket message."""
        try:
            message = json.loads(raw)
            msg_type = message.get("type", "")

            logger.debug(f"Received message: {msg_type}")

            if msg_type == "goal":
                await self._handle_goal(websocket, message)
            elif msg_type == "confirm":
                await self._handle_confirm(message, approved=True)
            elif msg_type == "deny":
                await self._handle_confirm(message, approved=False)
            elif msg_type == "stop":
                await self._handle_stop(websocket, message)
            elif msg_type == "system_info":
                await self._handle_system_info(websocket)
            elif msg_type == "ping":
                await self._connections.send_to(websocket, {
                    "type": "pong",
                    "timestamp": datetime.now().isoformat(),
                })
            else:
                logger.warning(f"Unknown message type: {msg_type}")

        except json.JSONDecodeError:
            logger.error(f"Invalid JSON received: {raw[:100]}")
            await self._connections.send_to(websocket, {
                "type": "error",
                "message": "Invalid message format",
            })

    async def _handle_goal(self, websocket: WebSocket, message: dict):
        """Handle a new goal from the user."""
        content = message.get("content", "")
        if not content:
            await self._connections.send_to(websocket, {
                "type": "error",
                "message": "Empty goal",
            })
            return

        logger.info(f"New goal: {content[:100]}")

        # Reset emergency stop if it was triggered
        if self._emergency_stop.is_stopped:
            self._emergency_stop.reset()

        # Create status callback that sends to this client
        async def status_callback(update: dict[str, Any]):
            update["timestamp"] = datetime.now().isoformat()
            await self._connections.send_to(websocket, update)

        # Run agent in background task
        task = asyncio.create_task(
            self._run_agent(content, status_callback)
        )
        
        # Register for emergency stop
        task_id = f"ws_{id(task)}"
        self._emergency_stop.register_task(task_id, task)
        
        # Don't await — runs in background while we keep receiving messages
        task.add_done_callback(
            lambda t: self._emergency_stop.unregister_task(task_id)
        )

    async def _run_agent(
        self, goal: str, status_callback
    ):
        """Run the agent loop for a goal."""
        try:
            result = await self._agent.process_goal(goal, status_callback)
            logger.info(f"Agent completed: {result.get('success')}")
        except asyncio.CancelledError:
            logger.warning("Agent task cancelled")
        except Exception as e:
            logger.error(f"Agent execution error: {e}")
            await status_callback({
                "type": "error",
                "message": f"Agent error: {str(e)}",
            })

    async def _handle_confirm(self, message: dict, approved: bool):
        """Handle user confirmation/denial of a permission request."""
        task_id = message.get("task_id", "")
        if task_id in self._pending_confirmations:
            future = self._pending_confirmations.pop(task_id)
            if not future.done():
                future.set_result(approved)
            logger.info(
                f"Confirmation {'approved' if approved else 'denied'}: {task_id}"
            )

    async def _handle_stop(self, websocket: WebSocket, message: dict):
        """Handle emergency stop request."""
        task_id = message.get("task_id")
        
        if task_id:
            await self._emergency_stop.stop_task(task_id)
            msg = f"Task {task_id} stopped"
        else:
            await self._emergency_stop.stop_all()
            msg = "All tasks stopped"
        
        logger.warning(f"Emergency stop: {msg}")
        await self._connections.send_to(websocket, {
            "type": "status",
            "state": AgentState.IDLE.value,
            "message": msg,
            "timestamp": datetime.now().isoformat(),
        })

    async def _handle_system_info(self, websocket: WebSocket):
        """Send system information to the client."""
        try:
            import psutil
            
            cpu = psutil.cpu_percent(interval=0.5)
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage("/")
            net = psutil.net_io_counters()
            
            battery = None
            try:
                bat = psutil.sensors_battery()
                if bat:
                    battery = {
                        "percent": bat.percent,
                        "charging": bat.power_plugged,
                    }
            except Exception:
                pass

            active_window = None
            try:
                import pygetwindow as gw
                aw = gw.getActiveWindow()
                if aw:
                    active_window = aw.title
            except Exception:
                pass

            await self._connections.send_to(websocket, {
                "type": "system_data",
                "data": {
                    "cpu_percent": cpu,
                    "memory_total": mem.total,
                    "memory_used": mem.used,
                    "memory_percent": mem.percent,
                    "disk_total": disk.total,
                    "disk_used": disk.used,
                    "disk_percent": disk.percent,
                    "network_sent": net.bytes_sent,
                    "network_recv": net.bytes_recv,
                    "battery": battery,
                    "active_window": active_window,
                    "process_count": len(psutil.pids()),
                },
                "timestamp": datetime.now().isoformat(),
            })
        except Exception as e:
            logger.error(f"System info error: {e}")

    async def request_user_confirmation(
        self,
        task_id: str,
        tool_name: str,
        description: str,
        parameters: dict,
    ) -> bool:
        """
        Request confirmation from the user for a tool execution.
        Returns True if approved, False if denied.
        Called by the PermissionManager.
        """
        future: asyncio.Future = asyncio.get_event_loop().create_future()
        self._pending_confirmations[task_id] = future

        await self._connections.broadcast({
            "type": "confirm_request",
            "task_id": task_id,
            "data": {
                "tool_name": tool_name,
                "description": description,
                "parameters": {
                    k: str(v)[:200] for k, v in parameters.items()
                },
            },
            "timestamp": datetime.now().isoformat(),
        })

        try:
            return await asyncio.wait_for(future, timeout=120.0)
        except asyncio.TimeoutError:
            self._pending_confirmations.pop(task_id, None)
            return False

"""
NEXA Backend — FastAPI Application Entry Point.

Starts the NEXA agent server with WebSocket support.
"""

from __future__ import annotations

import sys
import io

# Force UTF-8 encoding for Windows console to prevent charmap encoding errors
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "buffer"):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.agent.executor import Executor
from app.agent.loop import AgentLoop
from app.agent.observer import Observer
from app.agent.planner import Planner
from app.agent.recovery import RecoveryManager
from app.agent.verifier import Verifier
from app.ai.factory import get_llm_provider
from app.api.websocket_handler import ConnectionManager, WebSocketHandler
from app.config import get_settings
from app.memory.manager import MemoryManager
from app.security.audit import AuditLogger
from app.security.emergency import EmergencyStop
from app.security.permissions import PermissionManager
from app.tools.registry import ToolRegistry, discover_and_register_tools


# ─── Global State ───────────────────────────────────────────────────────────────

settings = get_settings()
connection_manager = ConnectionManager()
emergency_stop = EmergencyStop()

# These will be initialized in lifespan
agent_loop: AgentLoop | None = None
ws_handler: WebSocketHandler | None = None


# ─── Application Lifespan ──────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown."""
    global agent_loop, ws_handler

    logger.info("=" * 60)
    logger.info("  NEXA — Agentic AI Personal OS Assistant")
    logger.info("=" * 60)
    logger.info(f"Server: {settings.nexa_host}:{settings.nexa_port}")
    logger.info(f"LLM Provider: {settings.llm_provider.value}")
    logger.info(f"Log Level: {settings.nexa_log_level}")

    # ─── Initialize Components ──────────────────────────────────────

    # Tool Registry
    registry = ToolRegistry()
    discover_and_register_tools(registry)

    # Security
    permission_manager = PermissionManager(
        medium_risk_policy=settings.medium_risk_policy.value
    )
    audit_logger = AuditLogger(settings.audit_log_path)

    # Memory
    memory = MemoryManager(settings.memory_path)

    # AI Provider
    try:
        llm = get_llm_provider(settings)
        logger.info(f"LLM initialized: {llm.name} / {llm.model}")
    except ValueError as e:
        logger.warning(f"LLM not configured: {e}")
        logger.warning("Agent will operate in limited mode without AI.")
        llm = None

    # Agent Components
    if llm:
        planner = Planner(llm, registry.get_tool_descriptions())
        verifier = Verifier(llm)
    else:
        planner = None
        verifier = None

    executor = Executor(registry, permission_manager, audit_logger)
    observer = Observer(registry)
    recovery = RecoveryManager()

    # Agent Loop
    if llm and planner and verifier:
        agent_loop = AgentLoop(
            llm=llm,
            registry=registry,
            executor=executor,
            planner=planner,
            observer=observer,
            verifier=verifier,
            recovery=recovery,
            memory=memory,
            emergency_stop=emergency_stop,
            max_iterations=settings.max_agent_iterations,
        )

        # WebSocket Handler
        ws_handler = WebSocketHandler(
            agent_loop=agent_loop,
            emergency_stop=emergency_stop,
            connection_manager=connection_manager,
        )

        # Connect permission manager to WebSocket for confirmations
        permission_manager.set_confirmation_callback(
            ws_handler.request_user_confirmation
        )
    else:
        ws_handler = None

    logger.info(f"Tools registered: {registry.count}")
    logger.info(f"Agent ready: {agent_loop is not None}")
    logger.info("NEXA is online!")
    logger.info("=" * 60)

    yield  # Application is running

    # ─── Shutdown ───────────────────────────────────────────────────
    logger.info("Shutting down NEXA...")
    await emergency_stop.stop_all()
    logger.info("NEXA shutdown complete.")


# ─── FastAPI App ────────────────────────────────────────────────────────────────

app = FastAPI(
    title="NEXA",
    description="Agentic AI Personal OS Assistant",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api.scheduled_whatsapp import router as scheduled_whatsapp_router
app.include_router(scheduled_whatsapp_router)

from app.api.voice_transcribe import router as voice_transcribe_router
app.include_router(voice_transcribe_router)

from app.api.auto_reply import router as auto_reply_router
app.include_router(auto_reply_router)

from app.routers.ai_enhancer import router as ai_enhancer_router
app.include_router(ai_enhancer_router)


# ─── REST Endpoints ────────────────────────────────────────────────────────────

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "agent_ready": agent_loop is not None,
        "version": "0.1.0",
    }


@app.get("/api/system")
async def system_info():
    """Get system information."""
    import psutil
    
    cpu = psutil.cpu_percent(interval=0.5)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    
    return {
        "cpu_percent": cpu,
        "memory_percent": mem.percent,
        "memory_total_gb": round(mem.total / (1024**3), 2),
        "disk_percent": disk.percent,
        "process_count": len(psutil.pids()),
    }


@app.get("/api/tools")
async def list_tools():
    """List all available tools."""
    from app.tools.registry import ToolRegistry
    # Access from lifespan-initialized registry
    return {"tools": [], "message": "Use WebSocket for full interaction"}


# ─── WebSocket Endpoint ────────────────────────────────────────────────────────

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Main WebSocket endpoint for agent communication."""
    if ws_handler is None:
        await websocket.accept()
        await websocket.send_json({
            "type": "error",
            "message": (
                "NEXA agent is not configured. "
                "Please set up an LLM provider in .env file. "
                "See .env.example for options."
            ),
        })
        await websocket.close()
        return

    await ws_handler.handle_connection(websocket)


# ─── Run Server ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.nexa_host,
        port=settings.nexa_port,
        reload=True,
        log_level=settings.nexa_log_level.lower(),
    )

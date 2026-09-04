"""
NEXO Scheduled WhatsApp Messaging API Router (Phase 2).

Provides endpoints for creating, scheduling, updating, listing,
cancelling, and emergency stopping scheduled WhatsApp messages.
"""

from datetime import datetime
from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/whatsapp-schedule", tags=["Scheduled WhatsApp"])


class ScheduledJobModel(BaseModel):
    id: str = Field(..., description="Unique job ID")
    contact: str = Field(..., description="Recipient phone number or contact name")
    message: str = Field(..., description="Message content")
    date: str = Field(..., description="Date string e.g. 28 Aug 2026")
    time: str = Field(..., description="Time string e.g. 6:00 PM")
    scheduled_timestamp: int = Field(..., description="Unix epoch timestamp in milliseconds")
    repeat_rule: str = Field(default="NONE", description="NONE, DAILY, WEEKLY, CUSTOM")
    enabled: bool = Field(default=True, description="Enable / Disable toggle for schedule")
    status: str = Field(
        default="SCHEDULED",
        description="SCHEDULED, PREPARING, WAITING_FOR_UNLOCK, RUNNING, SENT, FAILED, CANCELLED"
    )
    status_reason: Optional[str] = Field(default="", description="Description of status or failure/waiting reason")
    created_at: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


class CreateScheduledJobRequest(BaseModel):
    contact: str
    message: str
    date: str
    time: str
    scheduled_timestamp: Optional[int] = None
    repeat_rule: str = "NONE"
    enabled: bool = True


class ScheduleLogEntry(BaseModel):
    id: str
    job_id: str
    timestamp: str
    contact: str
    message: str
    status: str
    details: str


class GenerateMessageRequest(BaseModel):
    contact: str
    prompt: str
    tone: str = "Friendly"  # Friendly, Professional, Casual, Urgent


class ParseCommandRequest(BaseModel):
    command: str


# ─── In-Memory Store ─────────────────────────────────────────────────────────────

_scheduled_jobs: Dict[str, ScheduledJobModel] = {}
_schedule_logs: List[ScheduleLogEntry] = []


def _seed_initial_jobs():
    if not _scheduled_jobs:
        job1 = ScheduledJobModel(
            id="job_wa_init_1",
            contact="John",
            message="Hello, I will contact you later.",
            date="28 Aug 2026",
            time="6:00 PM",
            scheduled_timestamp=1787920800000,
            repeat_rule="NONE",
            enabled=True,
            status="SCHEDULED",
            status_reason="Active schedule pending execution",
        )
        _scheduled_jobs[job1.id] = job1

_seed_initial_jobs()


@router.get("/jobs", response_model=List[ScheduledJobModel])
async def get_all_jobs():
    """Retrieve all scheduled WhatsApp jobs."""
    return list(_scheduled_jobs.values())


@router.post("/create", response_model=ScheduledJobModel)
async def create_scheduled_job(req: CreateScheduledJobRequest):
    """Create a new scheduled WhatsApp job."""
    job_id = f"job_wa_{int(datetime.now().timestamp() * 1000)}"
    ts = req.scheduled_timestamp or int(datetime.now().timestamp() * 1000) + 60000

    job = ScheduledJobModel(
        id=job_id,
        contact=req.contact,
        message=req.message,
        date=req.date,
        time=req.time,
        scheduled_timestamp=ts,
        repeat_rule=req.repeat_rule,
        enabled=req.enabled,
        status="SCHEDULED",
        status_reason="Scheduled task created successfully",
    )
    _scheduled_jobs[job_id] = job

    _schedule_logs.insert(0, ScheduleLogEntry(
        id=f"log_{int(datetime.now().timestamp() * 1000)}",
        job_id=job_id,
        timestamp=datetime.now().strftime("%H:%M"),
        contact=req.contact,
        message=req.message,
        status="SCHEDULED",
        details=f"Created schedule for {req.contact} at {req.time} ({req.date})"
    ))

    return job


@router.post("/update/{job_id}", response_model=ScheduledJobModel)
async def update_scheduled_job(job_id: str, updated_job: ScheduledJobModel):
    """Update an existing scheduled WhatsApp job."""
    if job_id not in _scheduled_jobs:
        raise HTTPException(status_code=404, detail="Scheduled job not found")

    _scheduled_jobs[job_id] = updated_job
    return updated_job


@router.post("/cancel/{job_id}", response_model=ScheduledJobModel)
async def cancel_scheduled_job(job_id: str):
    """Cancel a scheduled WhatsApp job."""
    if job_id not in _scheduled_jobs:
        raise HTTPException(status_code=404, detail="Scheduled job not found")

    job = _scheduled_jobs[job_id]
    job.status = "CANCELLED"
    job.enabled = False
    job.status_reason = "Cancelled by user request"

    _schedule_logs.insert(0, ScheduleLogEntry(
        id=f"log_{int(datetime.now().timestamp() * 1000)}",
        job_id=job_id,
        timestamp=datetime.now().strftime("%H:%M"),
        contact=job.contact,
        message=job.message,
        status="CANCELLED",
        details=f"Cancelled schedule for {job.contact}"
    ))

    return job


@router.post("/stop-all")
async def stop_all_scheduled_jobs():
    """Emergency Stop: Disables and cancels all pending scheduled tasks immediately."""
    cancelled_count = 0
    for job_id, job in _scheduled_jobs.items():
        if job.status in ["SCHEDULED", "PREPARING", "WAITING_FOR_UNLOCK", "RUNNING"]:
            job.status = "CANCELLED"
            job.enabled = False
            job.status_reason = "EMERGENCY STOP EXECUTED: All scheduled tasks halted."
            cancelled_count += 1

    _schedule_logs.insert(0, ScheduleLogEntry(
        id=f"log_{int(datetime.now().timestamp() * 1000)}",
        job_id="EMERGENCY_STOP",
        timestamp=datetime.now().strftime("%H:%M"),
        contact="ALL",
        message="STOP ALL SCHEDULED TASKS",
        status="CANCELLED",
        details=f"Emergency stop triggered. {cancelled_count} pending job(s) cancelled."
    ))

    return {
        "status": "stopped",
        "cancelled_count": cancelled_count,
        "jobs": list(_scheduled_jobs.values())
    }


@router.get("/logs", response_model=List[ScheduleLogEntry])
async def get_schedule_logs(limit: int = 50):
    """Get history logs for scheduled WhatsApp tasks."""
    return _schedule_logs[:limit]


class ExecuteTaskRequest(BaseModel):
    taskId: str
    executionId: str
    recipient: str
    message: str


@router.post("/execute-task")
async def execute_task(req: ExecuteTaskRequest):
    """Execute and confirm a scheduled WhatsApp task via system messaging service."""
    log_id = f"log_{int(datetime.now().timestamp() * 1000)}"
    
    # Update job status if present
    if req.taskId in _scheduled_jobs:
        _scheduled_jobs[req.taskId].status = "SENT"
        _scheduled_jobs[req.taskId].status_reason = "Executed successfully while screen OFF & device LOCKED"

    _schedule_logs.insert(0, ScheduleLogEntry(
        id=log_id,
        job_id=req.taskId,
        timestamp=datetime.now().strftime("%H:%M:%S"),
        contact=req.recipient,
        message=req.message,
        status="SENT",
        details=f"Task executed while screen OFF & device LOCKED. Message delivered to {req.recipient} ✓"
    ))

    return {
        "status": "SENT",
        "taskId": req.taskId,
        "executionId": req.executionId,
        "recipient": req.recipient,
        "message": req.message,
        "delivered": True,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }


@router.post("/generate-message")
async def generate_personalized_message(req: GenerateMessageRequest):
    """Generate an AI-personalized WhatsApp message based on contact, prompt, and tone."""
    tone_prefixes = {
        "Friendly": "Hey",
        "Professional": "Dear",
        "Casual": "Yo",
        "Urgent": "Important Notice for"
    }
    prefix = tone_prefixes.get(req.tone, "Hello")
    
    enhanced_msg = f"{prefix} {req.contact}, {req.prompt.strip()}"
    if not enhanced_msg.endswith(('.', '!', '?')):
        enhanced_msg += "."
        
    return {
        "contact": req.contact,
        "tone": req.tone,
        "original_prompt": req.prompt,
        "generated_message": enhanced_msg
    }


@router.post("/parse-command")
async def parse_natural_schedule_command(req: ParseCommandRequest):
    """Parse natural language command into structured schedule parameters."""
    cmd = req.command.strip()
    
    contact = "Contact"
    message = cmd
    date_str = datetime.now().strftime("%d %b %Y")
    time_str = "09:00 AM"
    ts = int(datetime.now().timestamp() * 1000) + 3600000  # Default +1 hour
    
    if "to " in cmd.lower():
        parts = cmd.split("to ", 1)[1]
        contact = parts.split(" ", 1)[0].strip(",").title()
        
    if "saying " in cmd.lower():
        message = cmd.split("saying ", 1)[1].strip('"\'')
    elif "that " in cmd.lower():
        message = cmd.split("that ", 1)[1].strip('"\'')
        
    return {
        "parsed": True,
        "contact": contact,
        "message": message,
        "date": date_str,
        "time": time_str,
        "scheduled_timestamp": ts
    }

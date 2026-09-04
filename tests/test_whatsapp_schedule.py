"""
Unit tests for Scheduled & Delayed WhatsApp Messaging.
"""

import pytest
import asyncio
from unittest.mock import patch
from app.tools.android.android_tools import (
    AndroidScheduleWhatsAppTool,
    AndroidListScheduledTool,
    AndroidCancelScheduledTool,
    parse_schedule_time,
    _SCHEDULED_WHATSAPP_JOBS,
)
from app.ai.rule_provider import RuleProvider


def test_parse_schedule_time():
    """Test relative delay and specific time parsing."""
    # Relative seconds
    dt1, sec1 = parse_schedule_time(delay_seconds=10)
    assert round(sec1) == 10

    # Relative string 'in 5 minutes'
    dt2, sec2 = parse_schedule_time(time_str="in 5 minutes")
    assert round(sec2) == 300

    # Specific time string '12:00 AM'
    dt3, sec3 = parse_schedule_time(time_str="at 12:00 AM")
    assert sec3 >= 0

    # Single hour formats 'at 9', 'at 9pm'
    dt4, sec4 = parse_schedule_time(time_str="at 9")
    assert sec4 > 0

    dt5, sec5 = parse_schedule_time(time_str="at 9pm")
    assert sec5 > 0


@pytest.mark.asyncio
async def test_android_schedule_whatsapp_tool_execution():
    """Test scheduling a job, listing it, and cancelling it."""
    schedule_tool = AndroidScheduleWhatsAppTool()
    list_tool = AndroidListScheduledTool()
    cancel_tool = AndroidCancelScheduledTool()

    # Schedule a message with short delay
    res = await schedule_tool.execute(phone="Jeskin", message="Happy Birthday!", time="in 60 seconds")
    assert res.success is True
    job_id = res.data["job_id"]
    assert job_id in _SCHEDULED_WHATSAPP_JOBS

    # List jobs
    list_res = await list_tool.execute()
    assert list_res.success is True
    assert list_res.data["count"] >= 1

    # Cancel job
    cancel_res = await cancel_tool.execute(job_id=job_id)
    assert cancel_res.success is True
    assert _SCHEDULED_WHATSAPP_JOBS[job_id]["status"] == "cancelled"


def test_rule_provider_scheduled_whatsapp_prompt():
    """Test RuleProvider intent extraction for scheduled WhatsApp prompts."""
    rp = RuleProvider()

    prompt = "Send 'Happy Birthday!' to Jeskin at 12:00 AM tonight on WhatsApp"
    plan = rp.generate_fallback_plan(prompt)
    assert len(plan.steps) == 1
    step = plan.steps[0]
    assert step.tool_name == "android.schedule_whatsapp"
    assert step.parameters["phone"] == "Jeskin"
    assert step.parameters["message"] == "Happy Birthday!"
    assert "time" in step.parameters

    # Test prompt with relative delay: 'send whatsapp message hi to Jeskin in 10 seconds'
    prompt2 = "send whatsapp message hi to Jeskin in 10 seconds"
    plan2 = rp.generate_fallback_plan(prompt2)
    assert len(plan2.steps) == 1
    step2 = plan2.steps[0]
    assert step2.tool_name == "android.schedule_whatsapp"
    assert step2.parameters["phone"] == "Jeskin"
    assert step2.parameters["message"] == "hi"
    assert "time" in step2.parameters


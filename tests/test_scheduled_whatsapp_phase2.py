"""
Verification test suite for Phase 2: NEXO Scheduled WhatsApp Messaging Module.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.ai.rule_provider import RuleProvider

client = TestClient(app)


# ─── 1. REST Endpoint & Status Lifecycle Verification ─────────────────────────

def test_get_all_scheduled_jobs():
    res = client.get("/api/whatsapp-schedule/jobs")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["contact"] == "John"
    assert data[0]["status"] == "SCHEDULED"


def test_create_scheduled_job():
    payload = {
        "contact": "John",
        "message": "Hello, I will contact you later.",
        "date": "28 Aug 2026",
        "time": "6:00 PM",
        "repeat_rule": "NONE",
        "enabled": True,
    }
    res = client.post("/api/whatsapp-schedule/create", json=payload)
    assert res.status_code == 200
    job = res.json()
    assert job["contact"] == "John"
    assert job["message"] == "Hello, I will contact you later."
    assert job["status"] == "SCHEDULED"
    assert job["repeat_rule"] == "NONE"


def test_cancel_scheduled_job():
    # First create
    create_res = client.post("/api/whatsapp-schedule/create", json={
        "contact": "Sarah",
        "message": "Meeting tomorrow",
        "date": "29 Aug 2026",
        "time": "9:00 AM",
    })
    job_id = create_res.json()["id"]

    # Cancel job
    cancel_res = client.post(f"/api/whatsapp-schedule/cancel/{job_id}")
    assert cancel_res.status_code == 200
    job = cancel_res.json()
    assert job["status"] == "CANCELLED"
    assert job["enabled"] is False


def test_emergency_stop_all_scheduled_tasks():
    # Create active jobs
    client.post("/api/whatsapp-schedule/create", json={
        "contact": "Contact A",
        "message": "Test A",
        "date": "28 Aug 2026",
        "time": "7:00 PM",
    })
    client.post("/api/whatsapp-schedule/create", json={
        "contact": "Contact B",
        "message": "Test B",
        "date": "28 Aug 2026",
        "time": "8:00 PM",
    })

    # Trigger Emergency Stop
    stop_res = client.post("/api/whatsapp-schedule/stop-all")
    assert stop_res.status_code == 200
    stop_data = stop_res.json()
    assert stop_data["status"] == "stopped"
    assert stop_data["cancelled_count"] >= 1

    # Verify all jobs are CANCELLED
    jobs_res = client.get("/api/whatsapp-schedule/jobs")
    for j in jobs_res.json():
        assert j["status"] == "CANCELLED" or j["enabled"] is False


def test_scheduled_whatsapp_history_logs():
    res = client.get("/api/whatsapp-schedule/logs")
    assert res.status_code == 200
    logs = res.json()
    assert isinstance(logs, list)
    assert len(logs) > 0


# ─── 2. Rule Provider Intent Parsing Verification ─────────────────────────────

def test_rule_provider_schedule_intent_parsing():
    rp = RuleProvider()

    prompt = "Send 'Hello, I will contact you later.' to John at 6:00 PM on 28 Aug 2026 on WhatsApp"
    plan = rp.generate_fallback_plan(prompt)
    assert len(plan.steps) == 1
    step = plan.steps[0]
    assert step.tool_name == "android.schedule_whatsapp"
    assert step.parameters["phone"] == "John"
    assert "Hello, I will contact you later." in step.parameters["message"]

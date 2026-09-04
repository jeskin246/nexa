"""
Verification test suite for Natural Language Commands and NEXO Auto-Reply.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.ai.rule_provider import RuleProvider

client = TestClient(app)


# ─── Natural Command Intent Verification ──────────────────────────────────────

def test_natural_command_whatsapp_single():
    rp = RuleProvider()

    prompt = "send whatsapp message 'Hello Jeskin' to +919876543210"
    plan = rp.generate_fallback_plan(prompt)
    assert len(plan.steps) == 1
    assert plan.steps[0].tool_name == "android.send_whatsapp"
    assert plan.steps[0].parameters["phone"] == "+919876543210"
    assert plan.steps[0].parameters["message"] == "Hello Jeskin"


def test_natural_command_whatsapp_multi():
    rp = RuleProvider()
    prompt = 'send whatsapp message to "hello" to jeskin and "hi" to anroe'
    plan = rp.generate_fallback_plan(prompt)
    assert len(plan.steps) == 1
    assert plan.steps[0].tool_name == "android.send_whatsapp"
    msgs = plan.steps[0].parameters["messages"]
    assert len(msgs) == 2
    assert msgs[0] == {"phone": "jeskin", "message": "hello"}
    assert msgs[1] == {"phone": "anroe", "message": "hi"}


def test_natural_command_whatsapp_scheduled():
    rp = RuleProvider()
    prompt = "send whatsapp message hi to Jeskin in 10 seconds"
    plan = rp.generate_fallback_plan(prompt)
    assert len(plan.steps) == 1
    assert plan.steps[0].tool_name == "android.schedule_whatsapp"
    assert plan.steps[0].parameters["phone"] == "Jeskin"
    assert plan.steps[0].parameters["message"] == "hi"
    assert "time" in plan.steps[0].parameters


def test_natural_command_youtube_share():
    rp = RuleProvider()
    prompt = "share vj siddhu vlogs video youtube to saritha in whatsapp"
    plan = rp.generate_fallback_plan(prompt)
    assert len(plan.steps) == 1
    assert plan.steps[0].tool_name == "android.send_whatsapp"
    assert plan.steps[0].parameters["phone"] == "saritha"
    assert "vj siddhu vlogs" in plan.steps[0].parameters["message"].lower()


def test_natural_command_app_launch():
    rp = RuleProvider()
    prompt = "open instagram on phone"
    plan = rp.generate_fallback_plan(prompt)
    assert len(plan.steps) == 1
    assert plan.steps[0].tool_name == "android.launch_app"
    assert plan.steps[0].parameters["name"] == "instagram"


# ─── Auto-Reply Endpoint Verification ───────────────────────────────────────

def test_auto_reply_full_flow():
    # 1. Fetch initial config
    res1 = client.get("/api/auto-reply/config")
    assert res1.status_code == 200
    cfg = res1.json()

    # 2. Update config to enabled with custom template
    new_payload = {
        "enabled": True,
        "user_status": "UNAVAILABLE",
        "waiting_time_seconds": 30,
        "cooldown_minutes": 5,
        "username": "Jeskin",
        "message_template": "Hey, Jeskin is currently unavailable.",
        "enabled_apps": {"WhatsApp": True, "Instagram": True},
    }
    res2 = client.post("/api/auto-reply/config", json=new_payload)
    assert res2.status_code == 200
    updated_cfg = res2.json()
    assert updated_cfg["enabled"] is True
    assert updated_cfg["username"] == "Jeskin"

    # 3. Add activity log entry
    log_entry = {
        "id": "test-log-101",
        "timestamp": "12:30",
        "app_name": "WhatsApp",
        "sender": "Alice",
        "message_text": "Are you free?",
        "stage": "replied",
        "details": "Sent auto reply to Alice",
        "reply_content": "Hey, Jeskin is currently unavailable.",
    }
    res3 = client.post("/api/auto-reply/logs", json=log_entry)
    assert res3.status_code == 200

    # 4. Fetch logs and verify entry
    res4 = client.get("/api/auto-reply/logs")
    assert res4.status_code == 200
    logs = res4.json()
    assert any(log["id"] == "test-log-101" for log in logs)

    # 5. Execute Emergency Stop
    res5 = client.post("/api/auto-reply/stop-all")
    assert res5.status_code == 200
    stop_data = res5.json()
    assert stop_data["status"] == "stopped"
    assert stop_data["config"]["enabled"] is False


def test_youtube_top_recent_high_views():
    rp = RuleProvider()

    # 1. Top video
    p1 = "play top video of dsa on youtube"
    plan1 = rp.generate_fallback_plan(p1)
    assert plan1.steps[0].tool_name == "android.play_youtube"
    assert plan1.steps[0].parameters["filter"] == "relevant"

    # 2. Recent video
    p2 = "play recent video of dsa on youtube"
    plan2 = rp.generate_fallback_plan(p2)
    assert plan2.steps[0].tool_name == "android.play_youtube"
    assert plan2.steps[0].parameters["filter"] == "recent"

    # 3. High view video
    p3 = "play high view video of dsa on youtube"
    plan3 = rp.generate_fallback_plan(p3)
    assert plan3.steps[0].tool_name == "android.play_youtube"
    assert plan3.steps[0].parameters["filter"] == "views"

    # 4. Most viewed video
    p4 = "play most viewed video of machine learning on youtube"
    plan4 = rp.generate_fallback_plan(p4)
    assert plan4.steps[0].tool_name == "android.play_youtube"
    assert plan4.steps[0].parameters["filter"] == "views"


def test_share_link_variations():
    rp = RuleProvider()

    # 1. Share video link
    p1 = "share link of dsa to saritha in whatsapp"
    plan1 = rp.generate_fallback_plan(p1)
    assert plan1.steps[0].tool_name == "android.send_whatsapp"
    assert plan1.steps[0].parameters["phone"] == "saritha"
    assert "https://www.youtube.com" in plan1.steps[0].parameters["message"]

    # 2. Share direct URL
    p2 = "share link https://github.com to saritha in whatsapp"
    plan2 = rp.generate_fallback_plan(p2)
    assert plan2.steps[0].tool_name == "android.send_whatsapp"
    assert plan2.steps[0].parameters["phone"] == "saritha"
    assert "https://github.com" in plan2.steps[0].parameters["message"]


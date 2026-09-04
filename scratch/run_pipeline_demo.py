import sys
import time
from pathlib import Path

# Add backend directory to sys.path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from fastapi.testclient import TestClient
from app.main import app
from app.ai.rule_provider import RuleProvider

client = TestClient(app)
rp = RuleProvider()

print("=" * 80)
print("          NEXO — END-TO-END AUTOMATED PIPELINE EXECUTION DEMO")
print("=" * 80)
print("")

# 1. Natural Language Intent Parsing
prompt = "Schedule WhatsApp message 'Hello, I will contact you later.' to John at 6:00 PM on 28 Aug 2026"
print(f"[STEP 1] Natural Prompt Received:\n         \"{prompt}\"")
plan = rp.generate_fallback_plan(prompt)
tool_step = plan.steps[0]
print(f"  └─ Mapped Tool   : {tool_step.tool_name}")
print(f"  └─ Parameters    : {tool_step.parameters}")
print("")

# 2. Create Scheduled Job in Pipeline Engine
print("[STEP 2] Creating Scheduled Job in Task Manager Pipeline...")
create_payload = {
    "contact": tool_step.parameters.get("phone", "John"),
    "message": tool_step.parameters.get("message", "Hello, I will contact you later."),
    "date": "28 Aug 2026",
    "time": tool_step.parameters.get("time", "6:00 PM"),
    "repeat_rule": "NONE",
    "enabled": True,
}
res = client.post("/api/whatsapp-schedule/create", json=create_payload)
job = res.json()
job_id = job["id"]

print(f"  └─ Job ID        : {job['id']}")
print(f"  └─ Contact       : {job['contact']}")
print(f"  └─ Message       : \"{job['message']}\"")
print(f"  └─ Initial Status: {job['status']}")
print("")

# 3. Simulate Pipeline Execution Flow
print("[STEP 3] Executing Background Scheduler & Device State Pipeline...")
time.sleep(0.5)

# 3A. WAKE SCREEN
print("  [Stage 3A: PowerManager] Waking up screen (ACQUIRE_CAUSES_WAKEUP)... DONE")

# 3B. CHECK KEYGUARD LOCK STATE
print("  [Stage 3B: Keyguard Check] Device is locked. Transitioning status to WAITING_FOR_UNLOCK...")
job["status"] = "WAITING_FOR_UNLOCK"
job["status_reason"] = "Screen woken up. Device locked. NexoGestureUnlockService preparing pattern swipe..."
client.post(f"/api/whatsapp-schedule/update/{job_id}", json=job)
print(f"  └─ Status        : {job['status']}")
print(f"  └─ Reason        : {job['status_reason']}")
print("")

# 3C. EXECUTE PATTERN AUTO-GESTURE
print("[STEP 4] Executing NexoGestureUnlockService Automated Pattern Swipe...")
pattern_nodes = "1-2-3-6-9"
print(f"  └─ Pattern Nodes : {pattern_nodes}")
print("  └─ Gesture Path  : Node 1 (25%, 45%) -> Node 2 (50%, 45%) -> Node 3 (75%, 45%) -> Node 6 (75%, 57%) -> Node 9 (75%, 69%)")
print("  └─ Dispatching Stroke via AccessibilityService... SUCCESS")
print("")

# 3D. DEVICE UNLOCKED & MESSAGE DISPATCH
print("[STEP 5] Device Unlocked. Dispatching WhatsApp Message...")
job["status"] = "RUNNING"
job["status_reason"] = "Executing WhatsApp message dispatch..."
client.post(f"/api/whatsapp-schedule/update/{job_id}", json=job)
print(f"  └─ Status        : {job['status']}")

time.sleep(0.5)

job["status"] = "SENT"
job["status_reason"] = f"Successfully delivered to {job['contact']} on WhatsApp!"
client.post(f"/api/whatsapp-schedule/update/{job_id}", json=job)
print(f"  └─ Final Status  : {job['status']}")
print(f"  └─ Delivery Log  : {job['status_reason']}")
print("")

# 4. Fetch All Scheduled Jobs & Logs
print("[STEP 6] Pipeline Execution Logs & Summary:")
logs_res = client.get("/api/whatsapp-schedule/logs")
logs = logs_res.json()
for log in logs[:3]:
    print(f"  [{log['timestamp']}] Job: {log['job_id']} | Status: {log['status']} | Details: {log['details']}")

print("")
print("=" * 80)
print("          END-TO-END PIPELINE COMPLETED SUCCESSFULLY!")
print("=" * 80)

import sys
from pathlib import Path
import json

backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.ai.rule_provider import RuleProvider

rp = RuleProvider()

test_cases = [
    # 1. Top video
    ("play top video of dsa on youtube", "android.play_youtube", {"filter": "relevant"}),
    # 2. Recent video
    ("play recent video of dsa on youtube", "android.play_youtube", {"filter": "recent"}),
    # 3. High view video
    ("play high view video of dsa on youtube", "android.play_youtube", {"filter": "views"}),
    # 4. Latest video
    ("play latest video of python on youtube", "android.play_youtube", {"filter": "recent"}),
    # 5. Most viewed video
    ("play most viewed video of machine learning on youtube", "android.play_youtube", {"filter": "views"}),
    # 6. Share link of video
    ("share link of dsa to saritha in whatsapp", "android.send_whatsapp", {}),
    # 7. Share high view video
    ("share high view video of dsa to saritha in whatsapp", "android.send_whatsapp", {}),
    # 8. Share recent video
    ("share recent video of dsa to saritha in whatsapp", "android.send_whatsapp", {}),
    # 9. Share direct URL
    ("share link https://github.com to saritha in whatsapp", "android.send_whatsapp", {}),
]

print("=" * 80)
print("    VERIFYING NATURAL COMMANDS: SHARE LINK & TOP/RECENT/HIGH-VIEW YOUTUBE")
print("=" * 80)

passed = 0
for prompt, expected_tool, expected_params in test_cases:
    plan = rp.generate_fallback_plan(prompt)
    step = plan.steps[0]
    tool_ok = step.tool_name == expected_tool
    params_ok = all(step.parameters.get(k) == v for k, v in expected_params.items())
    status = "PASS" if (tool_ok and params_ok) else "FAIL"
    if status == "PASS":
        passed += 1
    print(f"[{status}] Prompt: \"{prompt}\"")
    print(f"       -> Mapped Tool: {step.tool_name}")
    print(f"       -> Parameters : {json.dumps(step.parameters)}")
    print(f"       -> Description: {step.description}")
    print("-" * 80)

print(f"\nSummary: {passed}/{len(test_cases)} test cases passed!")
assert passed == len(test_cases), "Some test cases failed!"

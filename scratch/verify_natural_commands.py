import sys
from pathlib import Path

# Add backend directory to sys.path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.ai.rule_provider import RuleProvider
import json

rp = RuleProvider()

test_prompts = [
    'Schedule WhatsApp message "Hello, I will contact you later." to John at 6:00 PM on 28 Aug 2026',
    'send whatsapp message "Happy Birthday" to Jeskin at 12:00 AM tonight',
    'send whatsapp message hi to Sarah in 10 seconds',
    'list scheduled whatsapp messages',
    'cancel scheduled wa job_wa_1787920800000',
    'share vj siddhu vlogs video youtube to saritha in whatsapp'
]

print('================================================================================')
print('        NEXO PHASE 2 — SCHEDULED WHATSAPP MODULE VERIFICATION')
print('================================================================================\n')

for i, p in enumerate(test_prompts, 1):
    plan = rp.generate_fallback_plan(p)
    print(f'[{i}] Natural Prompt: "{p}"')
    for step in plan.steps:
        print(f'    -> Mapped Tool  : {step.tool_name}')
        print(f'    -> Parameters   : {json.dumps(step.parameters)}')
        print(f'    -> Description  : {step.description}')
    print('')

print('================================================================================')

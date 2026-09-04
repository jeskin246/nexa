"""
NEXA Agent System Tests.
"""

import pytest
from app.security.permissions import PermissionLevel, PermissionManager
from app.security.emergency import EmergencyStop


def test_permission_manager():
    pm = PermissionManager(medium_risk_policy="ask")
    policy = pm.get_policy("filesystem.search", PermissionLevel.LOW)
    assert policy.value == "auto"

    policy_med = pm.get_policy("filesystem.create", PermissionLevel.MEDIUM)
    assert policy_med.value == "ask"


def test_emergency_stop():
    es = EmergencyStop()
    assert es.is_stopped is False
    es.reset()
    assert es.is_stopped is False


@pytest.mark.asyncio
async def test_local_rule_provider():
    from app.ai.rule_provider import LocalRuleProvider
    from app.ai.base import LLMMessage

    provider = LocalRuleProvider()
    assert provider.name == "local_rules"

    # Test intent completion
    res = await provider.complete_structured(
        messages=[LLMMessage(role="user", content="Search computer for PDF files")],
        response_schema={"type": "object", "properties": {"category": {"type": "string"}}},
    )
    assert res["category"] == "search"

    # Test plan generation
    plan = await provider.complete_structured(
        messages=[LLMMessage(role="user", content="Take a screenshot")],
        response_schema={"type": "object", "properties": {"steps": {"type": "array"}}},
    )
    assert len(plan["steps"]) >= 1
    assert plan["steps"][0]["tool_name"] == "screen.capture"


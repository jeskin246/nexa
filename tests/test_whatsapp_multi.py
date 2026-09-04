"""
Tests for Multi-User WhatsApp Message Sending on Android.
"""

import pytest
from unittest.mock import patch, MagicMock
from app.tools.android.android_tools import AndroidSendWhatsAppTool
from app.ai.rule_provider import RuleProvider


@pytest.mark.asyncio
@patch("time.sleep")
async def test_android_send_whatsapp_multi_recipient_splitting(mock_sleep):
    """Test that AndroidSendWhatsAppTool splits multi-recipient strings correctly."""
    tool = AndroidSendWhatsAppTool()

    # Mock ADB runner so we don't attempt real device communication in unit test
    with patch("app.tools.android.android_tools.run_adb") as mock_adb:
        mock_adb.return_value = (0, "size: 1080x2400", "")

        # Test phone string with comma and 'and'
        result = await tool.execute(phone="Alice, Bob and Charlie", message="Hello team")
        assert result.success is True
        data = result.data
        assert data["count"] == 3
        phones = [r["phone"] for r in data["results"]]
        assert phones == ["Alice", "Bob", "Charlie"]


@pytest.mark.asyncio
@patch("time.sleep")
async def test_android_send_whatsapp_messages_list_expansion(mock_sleep):
    """Test that AndroidSendWhatsAppTool expands multi-recipient phone fields inside messages list."""
    tool = AndroidSendWhatsAppTool()

    with patch("app.tools.android.android_tools.run_adb") as mock_adb:
        mock_adb.return_value = (0, "", "")

        messages = [
            {"phone": "+1234567890, +9876543210", "message": "Notice"},
            {"phone": "Dave", "message": "Hi Dave"}
        ]
        result = await tool.execute(messages=messages)
        assert result.success is True
        assert result.data["count"] == 3
        phones = [r["phone"] for r in result.data["results"]]
        assert phones == ["+1234567890", "+9876543210", "Dave"]


def test_rule_provider_whatsapp_multi_recipient_parsing():
    """Test RuleProvider intent extraction for various multi-user WhatsApp prompts."""
    rp = RuleProvider()

    # Quoted messages to multiple recipients
    prompt1 = "send 'hi' to user1 and 'hello' to user2 on whatsapp"
    plan1 = rp.generate_fallback_plan(prompt1)
    assert len(plan1.steps) == 1
    assert plan1.steps[0].tool_name == "android.send_whatsapp"
    assert "messages" in plan1.steps[0].parameters
    assert len(plan1.steps[0].parameters["messages"]) == 2

    # Single message to multiple comma/and delimited recipients
    prompt2 = "send whatsapp message 'Meeting at 5' to Alice, Bob and +919876543210"
    plan2 = rp.generate_fallback_plan(prompt2)
    assert len(plan2.steps) == 1
    assert plan2.steps[0].tool_name == "android.send_whatsapp"
    assert "messages" in plan2.steps[0].parameters
    assert len(plan2.steps[0].parameters["messages"]) == 3
    recipients = [m["phone"] for m in plan2.steps[0].parameters["messages"]]
    assert recipients == ["Alice", "Bob", "+919876543210"]

    # Exact user prompt style: send whatsapp message to "hello" to jeskin and "hi" to anroe
    prompt3 = 'send whatsapp message to "hello" to jeskin and "hi" to anroe'
    plan3 = rp.generate_fallback_plan(prompt3)
    assert len(plan3.steps) == 1
    assert plan3.steps[0].tool_name == "android.send_whatsapp"
    msgs = plan3.steps[0].parameters["messages"]
    assert len(msgs) == 2
    assert msgs[0] == {"phone": "jeskin", "message": "hello"}
    assert msgs[1] == {"phone": "anroe", "message": "hi"}


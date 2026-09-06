"""
Tests for NEXA AI Text Enhancer Router.
"""

import asyncio
from app.routers.ai_enhancer import enhance_text, EnhanceRequest


def test_enhance_text_grammar_missing_am():
    req = EnhanceRequest(
        text="i jeskin",
        tone="grammar_fix",
    )
    res = asyncio.run(enhance_text(req))
    assert res.enhanced_text == "I am Jeskin."


def test_enhance_text_professional_intro():
    req = EnhanceRequest(
        text="i jeskin",
        tone="professional",
    )
    res = asyncio.run(enhance_text(req))
    assert "Jeskin" in res.enhanced_text
    assert "pleased" in res.enhanced_text or "name is" in res.enhanced_text


def test_enhance_text_friendly_intro():
    req = EnhanceRequest(
        text="i jeskin",
        tone="friendly",
    )
    res = asyncio.run(enhance_text(req))
    assert "Jeskin" in res.enhanced_text
    assert "😊" in res.enhanced_text


def test_enhance_text_japanese_translation():
    req = EnhanceRequest(
        text="i am jeskin",
        tone="translate",
        target_language="japanese",
    )
    res = asyncio.run(enhance_text(req))
    assert len(res.enhanced_text) > 0
    assert "ジェスキン" in res.enhanced_text or "日本語" in res.enhanced_text or "私" in res.enhanced_text

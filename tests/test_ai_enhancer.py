"""
Tests for NEXA AI Text Enhancer Router.
"""

import asyncio
from app.routers.ai_enhancer import enhance_text, EnhanceRequest


def test_enhance_text_professional():
    req = EnhanceRequest(
        text="i will come tommorow for the meting check the docs",
        tone="professional",
    )
    res = asyncio.run(enhance_text(req))
    assert "attend" in res.enhanced_text or "tomorrow" in res.enhanced_text
    assert res.tone == "professional"


def test_enhance_text_friendly():
    req = EnhanceRequest(
        text="are you free today",
        tone="friendly",
    )
    res = asyncio.run(enhance_text(req))
    assert "Hey!" in res.enhanced_text
    assert "😊" in res.enhanced_text


def test_enhance_text_grammar_fix():
    req = EnhanceRequest(
        text="pls send me the file asap thx",
        tone="grammar_fix",
    )
    res = asyncio.run(enhance_text(req))
    assert "please" in res.enhanced_text.lower()
    assert "thanks" in res.enhanced_text.lower() or "thank you" in res.enhanced_text.lower()


def test_enhance_text_translation():
    req = EnhanceRequest(
        text="Hello",
        tone="translate",
        target_language="tamil",
    )
    res = asyncio.run(enhance_text(req))
    assert len(res.enhanced_text) > 0

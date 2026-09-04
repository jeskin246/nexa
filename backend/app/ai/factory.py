"""
NEXA AI Factory — Creates the appropriate LLM provider from configuration.
"""

from __future__ import annotations

from loguru import logger

from app.ai.base import LLMProvider
from app.ai.rule_provider import LocalRuleProvider
from app.config import LLMProviderType, Settings


def get_llm_provider(settings: Settings) -> LLMProvider:
    """
    Factory function that creates an LLM provider based on configuration.
    
    If the requested cloud API provider (OpenAI, Gemini, Anthropic) lacks an API key,
    it gracefully falls back to the built-in LocalRuleProvider so NEXA runs
    100% offline out-of-the-box with ZERO API keys required!
    """
    provider_type = settings.llm_provider

    if provider_type == LLMProviderType.OPENAI:
        if settings.openai_api_key:
            from app.ai.openai_provider import OpenAIProvider
            logger.info(f"Creating OpenAI provider: {settings.openai_model}")
            return OpenAIProvider(
                api_key=settings.openai_api_key,
                model=settings.openai_model,
            )
        else:
            logger.warning("OPENAI_API_KEY not found. Using local offline rule provider.")
            return LocalRuleProvider()

    elif provider_type == LLMProviderType.GEMINI:
        if settings.gemini_api_key:
            from app.ai.gemini_provider import GeminiProvider
            logger.info(f"Creating Gemini provider: {settings.gemini_model}")
            return GeminiProvider(
                api_key=settings.gemini_api_key,
                model=settings.gemini_model,
            )
        else:
            logger.warning("GEMINI_API_KEY not found. Using local offline rule provider.")
            return LocalRuleProvider()

    elif provider_type == LLMProviderType.ANTHROPIC:
        if settings.anthropic_api_key:
            from app.ai.anthropic_provider import AnthropicProvider
            logger.info(
                f"Creating Anthropic provider: {settings.anthropic_model}"
            )
            return AnthropicProvider(
                api_key=settings.anthropic_api_key,
                model=settings.anthropic_model,
            )
        else:
            logger.warning("ANTHROPIC_API_KEY not found. Using local offline rule provider.")
            return LocalRuleProvider()

    elif provider_type == LLMProviderType.DEEPSEEK:
        if settings.deepseek_api_key:
            from app.ai.deepseek_provider import DeepSeekProvider
            logger.info(f"Creating DeepSeek provider: {settings.deepseek_model}")
            return DeepSeekProvider(
                api_key=settings.deepseek_api_key,
                base_url=settings.deepseek_base_url,
                model=settings.deepseek_model,
            )
        else:
            logger.warning("DEEPSEEK_API_KEY not found. Using local offline rule provider.")
            return LocalRuleProvider()

    elif provider_type == LLMProviderType.GROQ:
        if settings.groq_api_key:
            from app.ai.deepseek_provider import DeepSeekProvider
            logger.info(f"Creating Groq provider: {settings.groq_model}")
            return DeepSeekProvider(
                api_key=settings.groq_api_key,
                base_url=settings.groq_base_url,
                model=settings.groq_model,
            )
        else:
            logger.warning("GROQ_API_KEY not found. Using local offline rule provider.")
            return LocalRuleProvider()

    elif provider_type == LLMProviderType.OLLAMA:
        from app.ai.ollama_provider import OllamaProvider
        logger.info(
            f"Creating Ollama provider: {settings.ollama_model} "
            f"@ {settings.ollama_base_url}"
        )
        return OllamaProvider(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
        )

    # Default to LocalRuleProvider
    logger.info("Using default LocalRuleProvider")
    return LocalRuleProvider()

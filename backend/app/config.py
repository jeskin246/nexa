"""
NEXA Configuration — loaded from environment variables / .env file.
"""

from __future__ import annotations

import os
from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class LLMProviderType(str, Enum):
    OPENAI = "openai"
    GEMINI = "gemini"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"
    DEEPSEEK = "deepseek"
    GROQ = "groq"
    LOCAL_RULES = "local_rules"


class RiskPolicy(str, Enum):
    AUTO = "auto"
    ASK = "ask"
    BLOCKED = "blocked"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # --- Server ---
    nexa_host: str = "0.0.0.0"
    nexa_port: int = 8000
    nexa_log_level: str = "INFO"

    # --- LLM Provider ---
    llm_provider: LLMProviderType = LLMProviderType.OLLAMA

    # --- OpenAI ---
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o"

    # --- DeepSeek ---
    deepseek_api_key: Optional[str] = None
    deepseek_model: str = "deepseek-chat"
    deepseek_base_url: str = "https://api.deepseek.com"

    # --- Groq ---
    groq_api_key: Optional[str] = None
    groq_model: str = "llama-3.3-70b-versatile"
    groq_base_url: str = "https://api.groq.com/openai/v1"

    # --- Google Gemini ---
    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-2.0-flash"

    # --- Anthropic ---
    anthropic_api_key: Optional[str] = None
    anthropic_model: str = "claude-sonnet-4-20250514"

    # --- Ollama ---
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3"

    # --- Security ---
    medium_risk_policy: RiskPolicy = RiskPolicy.ASK
    audit_logging: bool = True
    max_agent_iterations: int = 20

    # --- Memory ---
    memory_file: str = "nexa_memory.json"

    # --- Browser ---
    browser_headless: bool = False
    browser_type: str = "chromium"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }

    @property
    def data_dir(self) -> Path:
        """Data directory for NEXA persistent storage."""
        d = Path.home() / ".nexa"
        d.mkdir(exist_ok=True)
        return d

    @property
    def audit_log_path(self) -> Path:
        return self.data_dir / "audit_log.jsonl"

    @property
    def memory_path(self) -> Path:
        return self.data_dir / self.memory_file


def get_settings() -> Settings:
    """Get cached settings instance."""
    # Look for .env in backend directory or project root
    backend_dir = Path(__file__).parent.parent
    project_root = backend_dir.parent
    
    env_paths = [
        backend_dir / ".env",
        project_root / ".env",
    ]
    
    for env_path in env_paths:
        if env_path.exists():
            os.environ.setdefault("ENV_FILE", str(env_path))
            return Settings(_env_file=str(env_path))
    
    return Settings()

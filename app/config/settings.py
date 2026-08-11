"""Configuration module for ClosePilot AI Sales Copilot."""
import os
from typing import Optional, Literal
from dotenv import load_dotenv, find_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Always locate and load the project .env file strictly
ENV_FILE_PATH = find_dotenv(usecwd=True) or os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.env"))
load_dotenv(ENV_FILE_PATH, override=True)


class Settings(BaseSettings):
    """Application runtime configuration settings loaded directly from .env."""
    APP_NAME: str = "ClosePilot AI Sales Copilot"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Server Settings
    BACKEND_HOST: str = "127.0.0.1"
    BACKEND_PORT: int = 8000
    
    # LLM Providers Configuration
    LLM_PROVIDER: str = "nvidia"
    LLM_MODEL: str = "meta/llama-3.1-70b-instruct"
    
    NVIDIA_API_KEY: Optional[str] = None
    NVIDIA_BASE_URL: str = "https://integrate.api.nvidia.com/v1"
    
    GROQ_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    
    # HubSpot MCP / API Configuration
    HUBSPOT_ACCESS_TOKEN: Optional[str] = None
    HUBSPOT_CLIENT_ID: Optional[str] = None
    HUBSPOT_CLIENT_SECRET: Optional[str] = None
    HUBSPOT_APP_ID: Optional[str] = None
    HUBSPOT_PORTAL_ID: Optional[str] = None
    HUBSPOT_USE_MOCK: bool = False
    
    # Supabase Database Configuration
    SUPABASE_URL: Optional[str] = None
    SUPABASE_KEY: Optional[str] = None

    # LangSmith Observability & Tracing Configuration
    LANGCHAIN_TRACING_V2: Optional[str] = None
    LANGCHAIN_API_KEY: Optional[str] = None
    LANGCHAIN_PROJECT: Optional[str] = "closepilot"
    LANGCHAIN_ENDPOINT: Optional[str] = "https://api.smith.langchain.com"
    LANGSMITH_API_KEY: Optional[str] = None
    LANGSMITH_PROJECT: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=ENV_FILE_PATH,
        env_file_encoding="utf-8",
        extra="ignore"
    )


def get_settings() -> Settings:
    """Dynamically reloads and returns latest settings directly from .env."""
    load_dotenv(ENV_FILE_PATH, override=True)
    s = Settings()
    
    # Ensure LangSmith tracing variables in os.environ match .env
    api_key = s.LANGSMITH_API_KEY or s.LANGCHAIN_API_KEY or os.environ.get("LANGCHAIN_API_KEY")
    project = s.LANGSMITH_PROJECT or s.LANGCHAIN_PROJECT or os.environ.get("LANGCHAIN_PROJECT") or "closepilot"
    
    if api_key:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = api_key
        os.environ["LANGCHAIN_PROJECT"] = project
        os.environ["LANGCHAIN_ENDPOINT"] = s.LANGCHAIN_ENDPOINT or "https://api.smith.langchain.com"

    return s


settings = get_settings()


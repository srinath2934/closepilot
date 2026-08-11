"""Configuration module for ClosePilot AI Sales Copilot."""
import os
from dotenv import load_dotenv, find_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Always locate and load the project .env file
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
    LLM_MODEL: str = "meta/llama-3.1-8b-instruct"
    
    NVIDIA_API_KEY: str = ""
    NVIDIA_BASE_URL: str = "https://integrate.api.nvidia.com/v1"
    
    GROQ_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    
    # HubSpot MCP / API Configuration
    HUBSPOT_ACCESS_TOKEN: str = ""
    HUBSPOT_CLIENT_ID: str = ""
    HUBSPOT_CLIENT_SECRET: str = ""
    HUBSPOT_APP_ID: str = ""
    HUBSPOT_PORTAL_ID: str = ""
    HUBSPOT_USE_MOCK: bool = False
    
    # Supabase Database Configuration
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""

    # LangSmith Observability & Tracing Configuration
    LANGCHAIN_TRACING_V2: str = "true"
    LANGCHAIN_API_KEY: str = ""
    LANGCHAIN_PROJECT: str = "closepilot"
    LANGCHAIN_ENDPOINT: str = "https://api.smith.langchain.com"

    model_config = SettingsConfigDict(
        env_file=ENV_FILE_PATH,
        env_file_encoding="utf-8",
        extra="ignore"
    )


def get_settings() -> Settings:
    """Dynamically reloads and returns latest settings directly from .env."""
    load_dotenv(ENV_FILE_PATH, override=True)
    s = Settings()
    
    # Export active LangChain / LangSmith variables to os.environ with non-blocking background ingestion
    if s.LANGCHAIN_API_KEY:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = s.LANGCHAIN_API_KEY
        os.environ["LANGCHAIN_PROJECT"] = s.LANGCHAIN_PROJECT
        os.environ["LANGCHAIN_ENDPOINT"] = s.LANGCHAIN_ENDPOINT
        os.environ["LANGCHAIN_CALLBACKS_BACKGROUND"] = "true"
        os.environ["LANGSMITH_TRACING_BACKGROUND"] = "true"
        os.environ["LANGSMITH_RUNS_ENDPOINTS_MAX_TIMEOUT"] = "1"

    return s


settings = get_settings()

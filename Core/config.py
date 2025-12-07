# Core/config.py
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from pathlib import Path
import os
# Load .env file

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

class Settings(BaseSettings):
    # Required APIs
    GROQ_API_KEY: str  # New: For Groq (primary now)
    OPENWEATHER_API_KEY: str
    OPENWEATHER_BASE_URL: str = "https://api.openweathermap.org/data/2.5"
   
    # LLM (now defaults to Groq-optimized model)
    LLM_MODEL: str = "llama3-groq-70b-8192-tool-use-preview"  # Fast tool-calling model
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 800

    # Old project leftovers (unchanged)
    APP_NAME: str = "WeatherChatBoT"
    APP_VERSION: str = "1.0.0"
    MCP_SERVER_HOST: str = "localhost"
    MCP_SERVER_PORT: str = "8001"
    FASTAPI_PORT: str = "8000"
    DEBUG: str = "False"

    model_config = {
        "extra": "allow",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }

settings = Settings()

print("\nWEATHER KEY →", settings.OPENWEATHER_API_KEY[:15] + "...")
print("GROQ KEY    →", settings.GROQ_API_KEY[:15] + "..." if settings.GROQ_API_KEY else "MISSING!")
print("MODEL       →", settings.LLM_MODEL)
print("APP STARTING — ALL SYSTEMS GO!\n")
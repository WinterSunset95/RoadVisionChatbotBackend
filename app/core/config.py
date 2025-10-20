"""
Loads and manages application configuration from environment variables using Pydantic.
"""
from pydantic import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """
    Pydantic BaseSettings class to validate and load environment variables.
    """
    DATABASE_URL: str
    GOOGLE_API_KEY: str
    LLAMA_CLOUD_API_KEY: Optional[str] = None

    class Config:
        env_file = ".env"

# Create a single instance of the settings to be imported across the app.
settings = Settings()



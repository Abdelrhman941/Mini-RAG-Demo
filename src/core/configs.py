from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    # ------------------ Application Configuration ------------------
    APP_NAME: str = "Mini-RAG"
    APP_VERSION: str = "0.1.0"
    APP_DESCRIPTION: str = "A mini RAG application for demo purposes."
    ENVIRONMENT: str = "local"

    # ------------------ File Upload Configuration ------------------
    FILE_ALLOWED_TYPES: list[str] = ["text/plain", "application/pdf"]
    FILE_MAX_SIZE: int = 10
    FILE_DEFAULT_CHUNK_SIZE: int = 512000  # bytes for reading uploaded files
    FILE_MAX_SIZE_SCALE: int = 1048576  # MB to bytes conversion (1MB = 1048576 bytes)
    CHUNK_SIZE_DEFAULT: int = 800
    OVERLAP_SIZE_DEFAULT: int = 100

    # ------------------ MongoDB Configuration ------------------
    MONGODB_URL: str
    MONGODB_DATABASE: str

    class Config:
        env_file = Path(__file__).resolve().parent.parent / ".env"
        env_file_encoding = "utf-8"

def get_settings():
    return Settings()

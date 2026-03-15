from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ------------------ Application Configuration ------------------
    APP_NAME: str = "Mini-RAG"
    APP_VERSION: str = "0.1.0"
    APP_DESCRIPTION: str = "A mini RAG application for demo purposes."
    ENVIRONMENT: str = "local"

    # ------------------ File Upload Configuration ------------------
    FILE_ALLOWED_TYPES: list[str] = ["text/plain", "application/pdf"]
    FILE_MAX_SIZE: int = 10
    FILE_DEFAULT_CHUNK_SIZE: int = 512000  # 512KB

    class Config:
        env_file = ".env"


def get_settings():
    return Settings()

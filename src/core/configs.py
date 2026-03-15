from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Mini-RAG"
    APP_VERSION: str = "0.1.0"
    APP_DESCRIPTION: str = "A mini RAG application for demo purposes."

    class Config:
        env_file = ".env"


def get_settings():
    return Settings()

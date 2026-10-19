from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    project_name: str = "Autonomous Living Knowledge Engine"

    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/shadowops"

    # OpenAI
    openai_api_key: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()

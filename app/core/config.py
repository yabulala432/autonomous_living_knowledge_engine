from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    project_name: str = "Autonomous Living Knowledge Engine"

    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/shadowops"

    # OpenAI
    openai_api_key: str = ""

    # GitHub
    github_token: str = ""

    # Telegram
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()

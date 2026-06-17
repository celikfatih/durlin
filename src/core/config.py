from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Jira Settings
    JIRA_URL: str
    JIRA_USER_EMAIL: str
    JIRA_API_TOKEN: str

    # GitHub Settings
    GITHUB_TOKEN: str = ""

    # Webhook Server Settings
    WEBHOOK_HOST: str = "0.0.0.0"
    WEBHOOK_PORT: int = 8000
    WEBHOOK_SECRET: str = ""
    WEBHOOK_VERIFY_SIGNATURE: bool = False
    TRIGGER_STATUS: str = "Ready-for-Test"

    # AI Settings
    AI_PROVIDER: str = "openai"
    AI_BASE_URL: str = "https://api.openai.com/v1"
    AI_API_KEY: str
    AI_MODEL_NAME: str = "gpt-4"
    AI_OUTPUT_LANGUAGE: str = "Turkish"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

def get_settings() -> Settings:
    return Settings()  # type: ignore

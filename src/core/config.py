from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Jira Settings
    JIRA_URL: str
    JIRA_USER_EMAIL: str
    JIRA_API_TOKEN: str

    # GitHub Settings
    GITHUB_TOKEN: str = ""

    # AI Settings
    AI_PROVIDER: str = "openai"
    AI_BASE_URL: str = "https://api.openai.com/v1"
    AI_API_KEY: str
    AI_MODEL_NAME: str = "gpt-4"
    AI_OUTPUT_LANGUAGE: str = "Turkish"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

def get_settings() -> Settings:
    return Settings()  # type: ignore

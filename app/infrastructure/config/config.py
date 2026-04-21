from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    telegram_bot_token: str
    openai_api_key: str
    vip_group_id: str = ""

    
    # Para el caso de Webhooks
    webhook_url: str = ""
    webhook_path: str = "/webhook"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

config = Settings()

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    telegram_bot_token: str
    openai_api_key: str
    vip_group_id: str = ""
    vip_channel_id: str = ""
    keycloak_url: str = ""
    keycloak_realm: str = ""
    keycloak_audience: str = "ApiTelegramProd"
    
    # Configuración de Webhook
    webhook_url: str = ""
    webhook_path: str = "/webhook"
    webhook_secret: str = "super_secret_token" # Opcional pero recomendado




    
    # URL de la API externa de datos (Vía Kong)
    external_data_api_url: str = "https://konge-dev.interrapidisimo.co/api/v1/data"

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra='ignore'
    )

config = Settings()

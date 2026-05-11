from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"

    gemini_api_key: str
    gemini_text_model: str = "gemini-2.5-flash"
    gemini_image_model: str = "gemini-2.5-flash-image"

    naver_client_id: str
    naver_client_secret: str
    naver_search_display: int = 20

    fitting_timeout_seconds: int = 60


settings = Settings()  # type: ignore[call-arg]

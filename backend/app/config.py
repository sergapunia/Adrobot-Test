from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    keitaro_base_url: str = ""
    keitaro_api_key: str = ""
    database_url: str = "sqlite:///./adrobot.db"
    cors_origins: str = "http://localhost:5173"
    campaign_name_prefix: str = "test_ukolov_"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()

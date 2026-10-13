from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "local"
    log_level: str = "INFO"
    database_url: str = "postgresql+asyncpg://root@localhost:5432/afrinograph_dev"
    test_database_url: str = "postgresql+asyncpg://root@localhost:5432/afrinograph_test"


settings = Settings()

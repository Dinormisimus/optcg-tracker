from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")

    APP_NAME: str = "One Piece TCG Tracker API"
    ENV: str = "dev"
    DATABASE_URL: str
    JWT_SECRET: str = "dev-secret-key"
    JWT_ISSUER: str = "sit-unizd"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7


settings = Settings()

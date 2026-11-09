from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "One Piece TCG Tracker API"
    ENV: str = "dev"
    DATABASE_URL: str
    JWT_SECRET: str = "dev-secret-key"
    JWT_ISSUER: str = "sit-unizd"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    class Config:
        env_file = "../.env"
        extra = "ignore"

settings = Settings()
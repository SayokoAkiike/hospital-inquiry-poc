from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Hospital Inquiry PoC"
    APP_ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "your-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/hospital_poc"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_DB: str = "hospital_poc"

    REDIS_URL: str = "redis://localhost:6379/0"

    ANTHROPIC_API_KEY: str = ""

    SLA_LOW: int = 72
    SLA_NORMAL: int = 24
    SLA_HIGH: int = 4
    SLA_URGENT: int = 1

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()

from pydantic_settings import BaseSettings

# 開発用フォールバック値。本番環境でこれらが残っていたら起動を拒否する。
_INSECURE_DEFAULT_SECRET_KEY = "your-secret-key"


class Settings(BaseSettings):
    APP_NAME: str = "Hospital Inquiry PoC"
    APP_ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = _INSECURE_DEFAULT_SECRET_KEY
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

    def validate_production_safety(self) -> None:
        """
        本番環境（APP_ENV=production）で危険なデフォルト設定のまま
        起動しようとしていないかをチェックする。

        医療系PoCとして、誤って開発用の値（デフォルトSECRET_KEYやDEBUG=true）
        が本番にデプロイされることは情報漏洩リスクが大きいため、
        起動時に早期に失敗（fail fast）させる方針とする。
        """
        if self.APP_ENV != "production":
            return

        errors: list[str] = []
        if self.SECRET_KEY == _INSECURE_DEFAULT_SECRET_KEY or not self.SECRET_KEY:
            errors.append(
                "SECRET_KEY がデフォルト値のままです。"
                '`python3 -c "import secrets; print(secrets.token_hex(32))"` '
                "で生成した値を環境変数で設定してください。"
            )
        if self.DEBUG:
            errors.append(
                "本番環境（APP_ENV=production）で DEBUG=true は許可されません。"
                "Swagger UI等が公開されるリスクがあります。DEBUG=false にしてください。"
            )
        if self.POSTGRES_PASSWORD in ("password", "", "CHANGE_ME"):
            errors.append(
                "POSTGRES_PASSWORD がデフォルト/プレースホルダー値のままです。"
                "本番用の強固なパスワードを設定してください。"
            )

        if errors:
            raise RuntimeError(
                "本番環境の設定に問題があるため起動を中止しました:\n"
                + "\n".join(f"- {e}" for e in errors)
            )


settings = Settings()
settings.validate_production_safety()

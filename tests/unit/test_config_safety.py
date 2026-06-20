"""
本番環境の危険なデフォルト設定を防ぐバリデーションのテスト。

development/test 環境では従来通り起動できること、
production 環境ではデフォルトSECRET_KEY等が拒否されることを確認する。
"""
import pytest

from app.core.config import Settings


def test_development_allows_default_secret_key():
    """開発環境ではデフォルトSECRET_KEYでも起動できる（開発体験を壊さない）。"""
    settings = Settings(APP_ENV="development", DEBUG=True, SECRET_KEY="your-secret-key")
    settings.validate_production_safety()  # 例外が出ないこと


def test_production_rejects_default_secret_key():
    """本番環境でデフォルトSECRET_KEYのままだと起動を拒否すること。"""
    settings = Settings(
        APP_ENV="production",
        DEBUG=False,
        SECRET_KEY="your-secret-key",
        POSTGRES_PASSWORD="strong-production-password",
    )
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        settings.validate_production_safety()


def test_production_rejects_debug_true():
    """本番環境でDEBUG=trueだと起動を拒否すること。"""
    settings = Settings(
        APP_ENV="production",
        DEBUG=True,
        SECRET_KEY="a-properly-generated-64-character-hex-secret-key-1234567890ab",
        POSTGRES_PASSWORD="strong-production-password",
    )
    with pytest.raises(RuntimeError, match="DEBUG"):
        settings.validate_production_safety()


def test_production_rejects_default_db_password():
    """本番環境でDBパスワードがデフォルトのままだと起動を拒否すること。"""
    settings = Settings(
        APP_ENV="production",
        DEBUG=False,
        SECRET_KEY="a-properly-generated-64-character-hex-secret-key-1234567890ab",
        POSTGRES_PASSWORD="password",
    )
    with pytest.raises(RuntimeError, match="POSTGRES_PASSWORD"):
        settings.validate_production_safety()


def test_production_accepts_proper_configuration():
    """本番環境でも適切に設定されていれば起動できること。"""
    settings = Settings(
        APP_ENV="production",
        DEBUG=False,
        SECRET_KEY="a-properly-generated-64-character-hex-secret-key-1234567890ab",
        POSTGRES_PASSWORD="strong-production-password",
    )
    settings.validate_production_safety()  # 例外が出ないこと

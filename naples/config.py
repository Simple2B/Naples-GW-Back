import os
from functools import lru_cache
import tomllib
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_ENV = os.environ.get("APP_ENV", "development")


def get_version() -> str:
    with open("pyproject.toml", "rb") as f:
        return tomllib.load(f)["tool"]["poetry"]["version"]


class BaseConfig(BaseSettings):
    """Base configuration."""

    ENV: str = "base"
    APP_NAME: str = "Naples Gateway"
    SECRET_KEY: str
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    WTF_CSRF_ENABLED: bool = False
    VERSION: str = get_version()

    # Super admin
    ADMIN_USERNAME: str
    ADMIN_EMAIL: str
    ADMIN_PASSWORD: str

    # API
    JWT_SECRET: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    # AWS
    AWS_SECRET_KEY: str | None
    AWS_ACCESS_KEY: str | None
    AWS_S3_BUCKET_NAME: str = "naples-gateway"
    AWS_REGION: str | None
    AWS_S3_BUCKET_URL: str
    # TODO: Add more AWS configurations
    # DEFAULT_IMAGE_URL: str

    # Stores URLs Discovery

    WEB_SERVICE_NAME: str = "naples-gw-front-app-1"
    CERT_RESOLVER: str = "myresolver"

    # mail configuration (gmail service)
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_DEFAULT_SENDER: str
    MAIL_SUBJECT: str = "Email Verification"
    MAIL_BODY_TEXT: str

    CHARSET: str = "UTF-8"

    REDIRECT_URL: str = "http://127.0.0.1:3000"
    REDIRECT_ROUTER_VERIFY_EMAIL: str = "/verify-email"
    REDIRECT_ROUTER_CHANGE_PASSWORD: str = "/change-password"

    # stripe
    STRIPE_SECRET_KEY: str
    STRIPE_PUBLIC_KEY: str
    STRIPE_WEBHOOK_KEY: str

    STRIPE_PRICE_STARTER_ID: str
    STRIPE_PRICE_PLUS_ID: str
    STRIPE_PRICE_PRO_ID: str

    model_config = SettingsConfigDict(
        extra="allow",
        env_file=("project.env", ".env.dev", ".env"),
    )


class DevelopmentConfig(BaseConfig):
    """Development configuration."""

    DEBUG: bool = True
    ALCHEMICAL_DATABASE_URL: str = "postgresql://postgres:passwd@127.0.0.1:15432/db"


class TestingConfig(BaseConfig):
    """Testing configuration."""

    TESTING: bool = True
    PRESERVE_CONTEXT_ON_EXCEPTION: bool = False
    ALCHEMICAL_DATABASE_URL: str = "sqlite:///" + os.path.join(BASE_DIR, "database-test.sqlite3")
    AWS_S3_BUCKET_NAME: str = "naples-gateway-test"
    MAIL_DEFAULT_SENDER: str = "sender@infotest.com"


class ProductionConfig(BaseConfig):
    """Production configuration."""

    ALCHEMICAL_DATABASE_URL: str = os.environ.get(
        "DATABASE_URL", "sqlite:///" + os.path.join(BASE_DIR, "database.sqlite3")
    )
    WTF_CSRF_ENABLED: bool = False


@lru_cache
def config(name: str = APP_ENV):
    CONF_MAP = dict(
        development=DevelopmentConfig,
        testing=TestingConfig,
        production=ProductionConfig,
    )
    configuration = CONF_MAP[name]()
    configuration.ENV = name
    return configuration

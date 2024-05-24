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

    # mail configuration
    MAIL_USERNAME: str = "Naples-GW"
    MAIL_HOST: str = "smtp.gmail.com"
    MAIL_PORT: int = 465
    MAIL_ADDRESS: str
    MAIL_PASSWORD: str
    MAIL_SUBJECT: str = "Email Verification"

    REDIRECT_URL: str = "http://127.0.0.1:3000/verify-email"

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

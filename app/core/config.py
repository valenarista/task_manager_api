from typing import TYPE_CHECKING

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"


if TYPE_CHECKING:
    settings = Settings(
        DATABASE_URL="",
        SECRET_KEY="",
        ALGORITHM="",
        ACCESS_TOKEN_EXPIRE_MINUTES=0,
    )
else:
    settings = Settings()

import logging

from pydantic_settings import BaseSettings, SettingsConfigDict

from src.settings.auth import AuthSettings
from src.settings.simulator import SimulatorSettings


class Settings(BaseSettings):
    log_level: str = "INFO"

    auth: AuthSettings
    sumo: SimulatorSettings = SimulatorSettings.model_construct()

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_nested_delimiter="__",
    )


settings = Settings()

logging.basicConfig(level=settings.log_level)
logging.debug(settings)

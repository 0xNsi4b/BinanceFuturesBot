from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr
from pathlib import Path

main_directory = Path(__file__).resolve().parent


class Settings(BaseSettings):
    key: SecretStr
    secret: SecretStr

    model_config = SettingsConfigDict(env_file=f'{main_directory}/.env', env_file_encoding='utf-8')


api = Settings()

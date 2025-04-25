from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        env_ignore_empty=True,
        frozen=True,
        extra="ignore"
    )

    DEBUG: bool

    DB_DRIVER: str ="postgresql+psycopg"
    DB_HOST: str
    DB_PORT: str
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str

    GOOGLE_CREDENTIALS: str
    GOOGLE_STORAGE_BUCKET: str

settings = Settings()
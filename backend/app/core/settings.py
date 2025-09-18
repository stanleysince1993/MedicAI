from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "MedicAI API"
    environment: str = "dev"
    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/medicai"
    # For MVP, timeseries can be the same DB; later enable TimescaleDB
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()

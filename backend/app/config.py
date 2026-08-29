from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://fms_ros:fms_ros@localhost:5432/fms_ros"
    tripletex_base_url: str = "https://tripletex.no/v2"
    tripletex_session_ttl_seconds: int = 3600
    solver_base_url: str = "http://localhost:8100"
    solver_time_limit_seconds: int = 30


settings = Settings()

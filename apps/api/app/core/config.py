from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="DASHFORGE_",
        env_file=(".env", "../../.env", "../../.env.example"),
        extra="ignore",
    )

    env: str = "local"
    database_url: str = "sqlite:///./storage/dashforge.db"
    storage_dir: Path = Path("./storage")
    allowed_origins: str = "http://localhost:3000"
    llm_provider: str = "none"
    llm_base_url: str = "https://api.openai.com/v1"
    llm_api_key: str = ""
    llm_model: str = "gpt-4.1-mini"
    router_base_url: str = "https://openrouter.ai/api/v1"
    router_api_key: str = ""
    router_model: str = "openai/gpt-4.1-mini"
    script_timeout_seconds: int = Field(default=20, ge=1, le=300)

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]

    @property
    def app_root(self) -> Path:
        return Path(__file__).resolve().parents[2]

    def ensure_storage(self) -> None:
        for name in ("raw", "staged", "cleaned", "artifacts", "executions"):
            (self.storage_dir / name).mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_storage()
    return settings


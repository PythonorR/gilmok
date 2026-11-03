"""Application settings, read from environment variables (see .env.example)."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(".env", "../../.env"), extra="ignore")

    database_url: str = "postgresql+psycopg://gilmok:gilmok@localhost:5432/gilmok"
    demo_mode: bool = True
    cors_origins: str = "http://localhost:3000"

    # Server-side credentials. Never returned in any response.
    data_go_kr_service_key: str = Field(default="", repr=False)
    seoul_open_api_key: str = Field(default="", repr=False)
    kakao_rest_api_key: str = Field(default="", repr=False)

    max_bbox_area_km2: float = 100.0
    cache_ttl_seconds: int = 86_400

    # Categories enabled in this release. Adding a category = data + score_config row + this list.
    enabled_categories: tuple[str, ...] = ("cafe",)

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

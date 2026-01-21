from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite:///data/ncaab.db"

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_ENABLED: bool = False  # Set to True when Redis is available

    # API
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "NCAA Basketball Analytics"

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
    ]

    # Cache
    CACHE_TTL: int = 300  # 5 minutes default
    CACHE_TTL_GAMES_TODAY: int = 60  # 1 minute for live games
    CACHE_TTL_HISTORICAL: int = 86400  # 24 hours for historical data

    # Pagination
    DEFAULT_PAGE_SIZE: int = 50
    MAX_PAGE_SIZE: int = 200

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

"""
Configuration module for the Hopper backend.

This module loads configuration from environment variables with sensible defaults.
"""

import os
from typing import Dict, Any, Optional
from pydantic import BaseSettings, Field

class DatabaseSettings(BaseSettings):
    """Database connection settings."""
    host: str = Field(default="localhost", env="DB_HOST")
    port: int = Field(default=5432, env="DB_PORT")
    username: str = Field(default="postgres", env="DB_USER")
    password: str = Field(default="postgres", env="DB_PASSWORD")
    database: str = Field(default="hopper", env="DB_NAME")
    
    @property
    def connection_string(self) -> str:
        """Get the database connection string."""
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"

class TimescaleDBSettings(DatabaseSettings):
    """TimescaleDB connection settings."""
    host: str = Field(default="localhost", env="TIMESCALE_HOST")
    port: int = Field(default=5432, env="TIMESCALE_PORT")
    username: str = Field(default="postgres", env="TIMESCALE_USER")
    password: str = Field(default="postgres", env="TIMESCALE_PASSWORD")
    database: str = Field(default="hopper_timeseries", env="TIMESCALE_DB_NAME")

class RedisSettings(BaseSettings):
    """Redis connection settings."""
    host: str = Field(default="localhost", env="REDIS_HOST")
    port: int = Field(default=6379, env="REDIS_PORT")
    db: int = Field(default=0, env="REDIS_DB")
    password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    
    @property
    def connection_string(self) -> str:
        """Get the Redis connection string."""
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"

class APISettings(BaseSettings):
    """API settings."""
    host: str = Field(default="0.0.0.0", env="API_HOST")
    port: int = Field(default=8000, env="API_PORT")
    debug: bool = Field(default=False, env="API_DEBUG")
    reload: bool = Field(default=False, env="API_RELOAD")
    workers: int = Field(default=4, env="API_WORKERS")
    cors_origins: str = Field(default="*", env="CORS_ORIGINS")

class MarketDataSettings(BaseSettings):
    """Market data provider settings."""
    finnhub_api_key: Optional[str] = Field(default=None, env="FINNHUB_API_KEY")
    alpha_vantage_api_key: Optional[str] = Field(default=None, env="ALPHA_VANTAGE_API_KEY")
    polygon_api_key: Optional[str] = Field(default=None, env="POLYGON_API_KEY")
    default_provider: str = Field(default="yfinance", env="DEFAULT_MARKET_DATA_PROVIDER")
    cache_ttl: int = Field(default=3600, env="MARKET_DATA_CACHE_TTL")  # 1 hour

class ValuationSettings(BaseSettings):
    """Valuation model settings."""
    default_risk_free_rate: float = Field(default=0.0425, env="DEFAULT_RISK_FREE_RATE")
    default_market_risk_premium: float = Field(default=0.05, env="DEFAULT_MARKET_RISK_PREMIUM")
    default_terminal_growth: float = Field(default=0.025, env="DEFAULT_TERMINAL_GROWTH")
    default_forecast_years: int = Field(default=5, env="DEFAULT_FORECAST_YEARS")

class Settings(BaseSettings):
    """Main application settings."""
    app_name: str = Field(default="Hopper Backend", env="APP_NAME")
    environment: str = Field(default="development", env="ENVIRONMENT")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Sub-settings
    database: DatabaseSettings = DatabaseSettings()
    timescale: TimescaleDBSettings = TimescaleDBSettings()
    redis: RedisSettings = RedisSettings()
    api: APISettings = APISettings()
    market_data: MarketDataSettings = MarketDataSettings()
    valuation: ValuationSettings = ValuationSettings()

# Create a global settings instance
settings = Settings()

def get_settings() -> Settings:
    """Get the application settings."""
    return settings 
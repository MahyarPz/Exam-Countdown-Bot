"""Configuration management for the bot."""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Bot configuration."""
    
    # Required
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    
    # Optional
    DEBUG_FAST_SCHEDULE: bool = os.getenv("DEBUG_FAST_SCHEDULE", "0") == "1"
    ADMIN_ID: int = int(os.getenv("ADMIN_ID", "0"))
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    DB_PATH: str = "exam_bot.db"  # Fallback for SQLite
    
    # Defaults
    DEFAULT_TIMEZONE: str = "Europe/Rome"
    DEFAULT_NOTIFY_TIME: str = "09:00"
    
    @classmethod
    def use_postgres(cls) -> bool:
        """Check if PostgreSQL should be used."""
        return bool(cls.DATABASE_URL)
    
    @classmethod
    def validate(cls) -> None:
        """Validate required configuration."""
        if not cls.BOT_TOKEN:
            raise ValueError("BOT_TOKEN environment variable is required")


# Validate on import
Config.validate()

"""Configuration management for the bot."""

import os
import json
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


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
    
    # Firestore
    USE_FIRESTORE: bool = os.getenv("USE_FIRESTORE", "0") == "1"
    FIREBASE_PROJECT_ID: str = os.getenv("FIREBASE_PROJECT_ID", "")
    GOOGLE_APPLICATION_CREDENTIALS: str = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
    FIREBASE_CREDENTIALS: str = os.getenv("FIREBASE_CREDENTIALS", "")
    
    # Defaults
    DEFAULT_TIMEZONE: str = "Europe/Rome"
    DEFAULT_NOTIFY_TIME: str = "09:00"
    
    @classmethod
    def _setup_firebase_credentials(cls) -> None:
        """Handle Firebase credentials from environment."""
        if not cls.use_firestore():
            return
        
        # If credentials are passed as JSON string (Heroku), save to file
        if cls.FIREBASE_CREDENTIALS and not cls.GOOGLE_APPLICATION_CREDENTIALS:
            try:
                cred_dict = json.loads(cls.FIREBASE_CREDENTIALS)
                cred_file = "/tmp/firebase-key.json"
                with open(cred_file, 'w') as f:
                    json.dump(cred_dict, f)
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = cred_file
                cls.GOOGLE_APPLICATION_CREDENTIALS = cred_file
                logger.info(f"Firebase credentials written to {cred_file}")
            except json.JSONDecodeError as e:
                logger.error(f"Invalid Firebase credentials JSON: {e}")
    
    @classmethod
    def use_postgres(cls) -> bool:
        """Check if PostgreSQL should be used."""
        return bool(cls.DATABASE_URL)
    
    @classmethod
    def use_firestore(cls) -> bool:
        """Check if Firestore should be used."""
        return cls.USE_FIRESTORE or bool(cls.FIREBASE_PROJECT_ID)
    
    @classmethod
    def validate(cls) -> None:
        """Validate required configuration."""
        if not cls.BOT_TOKEN:
            raise ValueError("BOT_TOKEN environment variable is required")
        
        if cls.use_firestore():
            if not cls.FIREBASE_PROJECT_ID:
                raise ValueError("FIREBASE_PROJECT_ID required when using Firestore")
            
            # Setup Firebase credentials from string if provided
            cls._setup_firebase_credentials()
            
            if not cls.GOOGLE_APPLICATION_CREDENTIALS or not os.path.exists(cls.GOOGLE_APPLICATION_CREDENTIALS):
                raise ValueError(
                    "GOOGLE_APPLICATION_CREDENTIALS file not found. "
                    "Either set GOOGLE_APPLICATION_CREDENTIALS path or FIREBASE_CREDENTIALS JSON string"
                )


# Validate on import
Config.validate()


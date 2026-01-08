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
    
    # Firestore - Support multiple naming conventions
    USE_FIRESTORE: bool = os.getenv("USE_FIRESTORE", "0") == "1"
    # Try multiple project ID env var names
    FIREBASE_PROJECT_ID: str = os.getenv("FIREBASE_PROJECT_ID", "") or os.getenv("GCP_PROJECT_ID", "")
    # Try multiple credentials env var names
    GOOGLE_APPLICATION_CREDENTIALS: str = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
    FIREBASE_CREDENTIALS: str = os.getenv("FIREBASE_CREDENTIALS", "") or os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON", "")
    
    # Defaults
    DEFAULT_TIMEZONE: str = "Europe/Rome"
    DEFAULT_NOTIFY_TIME: str = "09:00"
    
    @classmethod
    def _setup_firebase_credentials(cls) -> None:
        """Handle Firebase credentials from environment."""
        if not cls.use_firestore():
            return
        
        # Priority: Check if path already set
        if cls.GOOGLE_APPLICATION_CREDENTIALS and os.path.exists(cls.GOOGLE_APPLICATION_CREDENTIALS):
            logger.info(f"Using existing credentials file: {cls.GOOGLE_APPLICATION_CREDENTIALS}")
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = cls.GOOGLE_APPLICATION_CREDENTIALS
            return
        
        # Priority: Try to write JSON string to file
        if cls.FIREBASE_CREDENTIALS:
            try:
                cred_dict = json.loads(cls.FIREBASE_CREDENTIALS)
                cred_file = "/tmp/firebase-key.json"
                with open(cred_file, 'w') as f:
                    json.dump(cred_dict, f)
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = cred_file
                cls.GOOGLE_APPLICATION_CREDENTIALS = cred_file
                logger.info(f"Firebase credentials written to {cred_file}")
                return
            except json.JSONDecodeError as e:
                logger.error(f"Invalid Firebase credentials JSON: {e}")
                raise Exception(f"Invalid Firebase credentials: {e}")
        
        # If nothing worked
        raise Exception("No valid Firebase credentials found")
    
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
        
        # If Firestore is enabled, check if it's properly configured
        if cls.use_firestore():
            if not cls.FIREBASE_PROJECT_ID:
                logger.warning("FIREBASE_PROJECT_ID / GCP_PROJECT_ID not set, falling back to SQLite")
                cls.USE_FIRESTORE = False
                return
            
            if not cls.GOOGLE_APPLICATION_CREDENTIALS and not cls.FIREBASE_CREDENTIALS:
                logger.warning("Firebase credentials not found, falling back to SQLite")
                cls.USE_FIRESTORE = False
                return
            
            try:
                cls._setup_firebase_credentials()
            except Exception as e:
                logger.warning(f"Failed to setup Firebase credentials: {e}. Falling back to SQLite")
                cls.USE_FIRESTORE = False
                return
        
        # Log which database is being used
        if cls.use_firestore():
            logger.info(f"✅ Using Firestore database (Project: {cls.FIREBASE_PROJECT_ID})")
        elif cls.use_postgres():
            logger.info("✅ Using PostgreSQL database")
        else:
            logger.info("✅ Using SQLite database (local)")


# Validate on import
Config.validate()


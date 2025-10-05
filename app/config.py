import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class StorageConfig:
    """Storage service configuration"""

    # Server configuration
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8005))
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"

    # Storage paths
    STORAGE_BASE_PATH = Path(os.getenv("STORAGE_BASE_PATH", "./data"))

    # File limits
    MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 52428800))  # 50MB
    ALLOWED_EXTENSIONS = set(os.getenv("ALLOWED_EXTENSIONS", "jpg,jpeg,png,gif,webp,mp4,webm,mov,avi,mkv,mp3,wav,m4a,aac,pdf,pptx,ppt,docx,doc").split(","))

    # API security
    API_KEY = os.getenv("API_KEY", "storage_service_secret_key_2024")

    # Cleanup settings
    AUTO_CLEANUP_ENABLED = os.getenv("AUTO_CLEANUP_ENABLED", "True").lower() == "true"
    CLEANUP_OLDER_THAN_DAYS = int(os.getenv("CLEANUP_OLDER_THAN_DAYS", 30))
    CLEANUP_INTERVAL_HOURS = int(os.getenv("CLEANUP_INTERVAL_HOURS", 24))

    @classmethod
    def create_directories(cls):
        """Create necessary storage directories"""
        # Main storage directories
        directories = [
            cls.STORAGE_BASE_PATH,
            cls.STORAGE_BASE_PATH / "web",
            cls.STORAGE_BASE_PATH / "ai",
            cls.STORAGE_BASE_PATH / "presentai",
            cls.STORAGE_BASE_PATH / "office",
            cls.STORAGE_BASE_PATH / "uploads",
            cls.STORAGE_BASE_PATH / "media",
            cls.STORAGE_BASE_PATH / "temp",
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            print(f"📁 Created directory: {directory}")

# Global config instance
config = StorageConfig()
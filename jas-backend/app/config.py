import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings:
    """Application configuration settings"""

    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    _DEFAULT_DB_URL: str = f"sqlite:///{(BASE_DIR / 'test.db').as_posix()}"

    @classmethod
    def _resolve_database_url(cls, raw_url: str | None) -> str:
        if not raw_url:
            return cls._DEFAULT_DB_URL

        # Convert cwd-relative sqlite URLs (sqlite:///./...) into stable backend-root paths.
        if raw_url.startswith("sqlite:///./"):
            rel_part = raw_url.replace("sqlite:///./", "", 1)
            return f"sqlite:///{(cls.BASE_DIR / rel_part).as_posix()}"

        return raw_url
    
    # Database
    DATABASE_URL: str = _DEFAULT_DB_URL
    
    # OCR
    TESSERACT_CMD: str = os.getenv(
        "TESSERACT_CMD",
        r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    )
    
    # File storage
    DOCUMENTS_DIR: str = os.getenv(
        "DOCUMENTS_DIR",
        "data/documents"
    )
    
    # API
    MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "50"))
    MAX_FILES_PER_UPLOAD: int = int(os.getenv("MAX_FILES_PER_UPLOAD", "5"))
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    def __init__(self):
        """Initialize settings and create required directories"""
        self.DATABASE_URL = self._resolve_database_url(os.getenv("DATABASE_URL"))
        os.makedirs(self.DOCUMENTS_DIR, exist_ok=True)


settings = Settings()

import os
from pathlib import Path
from pydantic_settings import BaseSettings

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    PROJECT_NAME: str = "CollegeConnect AI - VVCE"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"

    # College details
    COLLEGE_NAME: str = "Vidyavardhaka College of Engineering"
    COLLEGE_SHORT_NAME: str = "VVCE"
    COLLEGE_BASE_URL: str = "https://vvce.ac.in"
    OFFICIAL_CONTACT_EMAIL: str = "info@vvce.ac.in"
    OFFICIAL_CONTACT_PHONE: str = "+91 821 4276201"

    # Gemini API
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"
    GEMINI_EMBEDDING_MODEL: str = "text-embedding-004"

    # Vector Storage
    CHROMA_PERSIST_DIR: str = str(BASE_DIR / "data" / "chromadb")
    COLLECTION_NAME: str = "vvce_knowledge_base"

    # Data paths
    RAW_DATA_DIR: str = str(BASE_DIR / "data" / "raw")
    PROCESSED_DATA_DIR: str = str(BASE_DIR / "data" / "processed")

    # Security & Rate Limiting
    ADMIN_API_KEY: str = "vvce_admin_secret_key_change_me"
    RATE_LIMIT_PER_MINUTE: str = "20/minute"
    ALLOWED_ORIGINS: str = "*"

    # Grounding & Sufficiency Thresholds
    EVIDENCE_THRESHOLD: float = 0.65
    TOP_K_RETRIEVAL: int = 4

    def get_chroma_dir(self) -> str:
        p = Path(self.CHROMA_PERSIST_DIR)
        return str(p if p.is_absolute() else (BASE_DIR / p).resolve())

    def get_raw_dir(self) -> str:
        p = Path(self.RAW_DATA_DIR)
        return str(p if p.is_absolute() else (BASE_DIR / p).resolve())

    def get_processed_dir(self) -> str:
        p = Path(self.PROCESSED_DATA_DIR)
        return str(p if p.is_absolute() else (BASE_DIR / p).resolve())

    class Config:
        env_file = str(BASE_DIR / ".env")
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()

# Ensure critical data directories exist
os.makedirs(settings.get_chroma_dir(), exist_ok=True)
os.makedirs(settings.get_raw_dir(), exist_ok=True)
os.makedirs(settings.get_processed_dir(), exist_ok=True)

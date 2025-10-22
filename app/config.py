import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

class Settings:
    # Paths
    ROOT_DIR: Path = Path(__file__).parent.parent.resolve()
    CHROMA_PATH: Path = ROOT_DIR / "chroma_db"
    DATA_DIR: Path = ROOT_DIR / "data"

    # Document Processing
    MAX_CHUNKS_PER_DOCUMENT: int = 2000
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    MAX_PDFS_PER_CHAT: int = 5
    MAX_EXCEL_PER_CHAT: int = 2
    MAX_PDF_SIZE_MB: int = 50
    MAX_EXCEL_SIZE_MB: int = 10

    # RAG
    RAG_TOP_K: int = 15

    # API Keys
    GOOGLE_API_KEY: str = ""
    LLAMA_CLOUD_API_KEY: str = ""
    
    # Database
    MONGODB_USER: str = "mongo"
    MONGODB_PASSWORD: str = "mongo"
    MONGODB_DB: str = "mongo"
    MONGODB_HOST: str = "localhost"  # Default for local scripts. Override with MONGODB_HOST=db for Docker.
    MONGODB_PORT: int = 27017
    MONGODB_URL: str = "localhost"
    
    # Environment
    ENV: str = "development"

    def __init__(self):
        self._load_and_validate_env()

    def _load_and_validate_env(self):
        """Load and validate environment variables"""
        print("🔍 Loading environment variables...")
        
        env_path = self.ROOT_DIR / '.env'
        if env_path.exists():
            load_dotenv(dotenv_path=env_path, verbose=True)
        else:
            load_dotenv(verbose=True)

        self.GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
        self.LLAMA_CLOUD_API_KEY = os.getenv("LLAMA_CLOUD_API_KEY")
        
        self.MONGODB_USER = os.getenv("MONGODB_INITDB_ROOT_USERNAME")
        self.MONGODB_PASSWORD = os.getenv("MONGODB_INITDB_ROOT_PASSWORD")
        self.MONGODB_DB = os.getenv("MONGODB_INITDB_DATABASE")
        self.MONGODB_HOST = os.getenv("MONGODB_HOST", self.MONGODB_HOST)

        if not self.GOOGLE_API_KEY:
            raise ValueError("❌ GOOGLE_API_KEY not found in environment!")
        
        if not all([self.MONGODB_USER, self.MONGODB_PASSWORD, self.MONGODB_DB]):
            raise ValueError("❌ Missing MongoDB connection details in environment!")

        self.MONGODB_URL = (
            f"mongodb://{self.MONGODB_USER}:{self.MONGODB_PASSWORD}"
            f"@{self.MONGODB_HOST}:{self.MONGODB_PORT}/"
        )
        
        print(f"✅ GOOGLE_API_KEY: configured")
        print(f"✅ LLAMA_CLOUD_API_KEY: {'configured' if self.LLAMA_CLOUD_API_KEY else 'not configured (optional)'}")
        print(f"✅ MongoDB: configured at {self.MONGODB_HOST}:{self.MONGODB_PORT}")

# Singleton instance
settings = Settings()

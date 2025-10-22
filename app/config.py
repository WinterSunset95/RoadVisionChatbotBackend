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
    MONGO_USER: str = "mongo"
    MONGO_PASSWORD: str = "mongo"
    MONGO_DB: str = "mongo"
    MONGO_HOST: str = "localhost"  # Default for local scripts. Override with MONGO_HOST=db for Docker.
    MONGO_PORT: int = 27017
    MONGO_URL: str = "localhost"
    
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

        google_api_key = os.getenv("GOOGLE_API_KEY")
        if not google_api_key:
            raise Exception("❌ GOOGLE_API_KEY not found in environment!")
        self.GOOGLE_API_KEY = google_api_key

        llama_api_key = os.getenv("LLAMA_CLOUD_API_KEY")
        if not llama_api_key:
            raise Exception("❌ LLAMA_CLOUD_API_KEY not found in environment!")
        self.LLAMA_CLOUD_API_KEY = llama_api_key
        
        mongo_root_user = os.getenv("MONGO_INITDB_ROOT_USERNAME")
        if not mongo_root_user:
            raise Exception("❌ MONGO_INITDB_ROOT_USERNAME not found in environment!")
        self.MONGO_USER = mongo_root_user

        mongo_root_password = os.getenv("MONGO_INITDB_ROOT_PASSWORD")
        if not mongo_root_password:
            raise Exception("❌ MONGO_INITDB_ROOT_PASSWORD not found in environment!")
        self.MONGO_PASSWORD = mongo_root_password

        mongo_database = os.getenv("MONGO_INITDB_DATABASE")
        if not mongo_database:
            raise Exception("❌ MONGO_INITDB_DATABASE not found in environment!")
        self.MONGO_DB = mongo_database

        self.MONGO_PORT = int(os.getenv("MONGO_PORT", 27017))
        self.MONGO_HOST = os.getenv("MONGO_HOST", self.MONGO_HOST)

        if not self.GOOGLE_API_KEY:
            raise ValueError("❌ GOOGLE_API_KEY not found in environment!")
        
        if not all([self.MONGO_USER, self.MONGO_PASSWORD, self.MONGO_DB]):
            raise ValueError("❌ Missing MongoDB connection details in environment!")

        self.MONGO_URL = (
            f"mongodb://{self.MONGO_USER}:{self.MONGO_PASSWORD}"
            f"@{self.MONGO_HOST}:{self.MONGO_PORT}/?authSource=admin"
        )
        
        print(f"✅ GOOGLE_API_KEY: configured")
        print(f"✅ LLAMA_CLOUD_API_KEY: {'configured' if self.LLAMA_CLOUD_API_KEY else 'not configured (optional)'}")
        print(f"✅ MongoDB: configured at {self.MONGO_HOST}:{self.MONGO_PORT}")

# Singleton instance
settings = Settings()

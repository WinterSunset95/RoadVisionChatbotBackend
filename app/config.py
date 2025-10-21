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
    LLAMA_CLOUD_API_KEY: Optional[str] = None
    
    # Database
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_DB: Optional[str] = None
    POSTGRES_HOST: str = "db"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: Optional[str] = None
    
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

        self.GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
        self.LLAMA_CLOUD_API_KEY = os.getenv("LLAMA_CLOUD_API_KEY")
        
        self.POSTGRES_USER = os.getenv("POSTGRES_USER")
        self.POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
        self.POSTGRES_DB = os.getenv("POSTGRES_DB")

        if not self.GOOGLE_API_KEY:
            raise ValueError("❌ GOOGLE_API_KEY not found in environment!")
        
        if not all([self.POSTGRES_USER, self.POSTGRES_PASSWORD, self.POSTGRES_DB]):
            raise ValueError("❌ Missing PostgreSQL connection details in environment!")

        self.DATABASE_URL = (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )
        
        print(f"✅ GOOGLE_API_KEY: configured")
        print(f"✅ LLAMA_CLOUD_API_KEY: {'configured' if self.LLAMA_CLOUD_API_KEY else 'not configured (optional)'}")
        print(f"✅ PostgreSQL DB: configured at {self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}")

# Singleton instance
settings = Settings()

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
    
    # PostgreSQL
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "postgres"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/postgres"

    # Security
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_SECRET_KEY: str = "secret"
    ALGORITHM: str = "HS256"
    
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
        
        # Load PostgreSQL settings
        self.POSTGRES_USER = os.getenv("POSTGRES_USER", self.POSTGRES_USER)
        self.POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", self.POSTGRES_PASSWORD)
        self.POSTGRES_DB = os.getenv("POSTGRES_DB", self.POSTGRES_DB)
        self.POSTGRES_HOST = os.getenv("POSTGRES_HOST", self.POSTGRES_HOST)
        self.POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", self.POSTGRES_PORT))

        self.DATABASE_URL = (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )
        
        print(f"✅ GOOGLE_API_KEY: configured")
        print(f"✅ LLAMA_CLOUD_API_KEY: {'configured' if self.LLAMA_CLOUD_API_KEY else 'not configured (optional)'}")
        print(f"✅ PostgreSQL: configured at {self.POSTGRES_HOST}:{self.POSTGRES_PORT}")

        # Load security settings
        jwt_secret_key = os.getenv("JWT_SECRET_KEY")
        if not jwt_secret_key:
            raise Exception("❌ JWT_SECRET_KEY not found in environment!")
        self.JWT_SECRET_KEY = jwt_secret_key

        algorithm = os.getenv("JWT_ALGORITHM")
        if not algorithm:
            raise Exception("❌ JWT_ALGORITHM not found in environment!")
        self.ALGORITHM = algorithm

# Singleton instance
settings = Settings()

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
        
        if not self.GOOGLE_API_KEY:
            raise ValueError("❌ GOOGLE_API_KEY not found in environment!")
        
        print(f"✅ GOOGLE_API_KEY: configured")
        print(f"✅ LLAMA_CLOUD_API_KEY: {'configured' if self.LLAMA_CLOUD_API_KEY else 'not configured (optional)'}")

# Singleton instance
settings = Settings()

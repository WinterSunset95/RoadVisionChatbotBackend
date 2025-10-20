"""
Moves the static configuration class into a dedicated file.
This separates static, hardcoded config from dynamic environment-based config.
"""
from pathlib import Path

class AppConfig:
    """
    Static application configuration settings.
    """
    CHROMA_PATH = Path("./chroma_db").resolve()
    MAX_CHUNKS_PER_DOCUMENT = 2000
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200
    MAX_PDFS_PER_CHAT = 5
    MAX_EXCEL_PER_CHAT = 2
    RAG_TOP_K = 15
    MAX_PDF_SIZE_MB = 50
    MAX_EXCEL_SIZE_MB = 10

# Create a single instance to be used throughout the application.
settings = AppConfig()

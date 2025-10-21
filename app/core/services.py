import tiktoken
import chromadb
from chromadb.config import Settings
import google.generativeai as genai
from sentence_transformers import SentenceTransformer
from llama_parse import LlamaParse

from app.config import settings
from app.services.document_service import PDFProcessor, ExcelProcessor
from app.db.vector_store import VectorStoreManager
# document_store is replaced by DB CRUD operations

print("--- Initializing Core Services ---")

try:
    genai.configure(api_key=settings.GOOGLE_API_KEY)
    llm_model = genai.GenerativeModel("gemini-2.0-flash-exp")
    print("✅ Gemini 2.0 Flash configured")

    embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
    print("✅ SentenceTransformer loaded")
    
    chroma_client = chromadb.PersistentClient(
        path=str(settings.CHROMA_PATH),
        settings=Settings(anonymized_telemetry=False, allow_reset=True)
    )
    print(f"✅ ChromaDB initialized at {settings.CHROMA_PATH}")
    
    tokenizer = tiktoken.get_encoding("cl100k_base")

    pdf_processor = PDFProcessor(embedding_model, tokenizer)
    excel_processor = ExcelProcessor(embedding_model, tokenizer) 
    vector_store = VectorStoreManager(chroma_client, embedding_model)
    
    # This mimics the legacy global state for now. Will be replaced in Phase 3 with Redis.
    upload_jobs: dict = {}
    # active_conversations and document_store are now handled by the database.

    print("--- Core Services Initialized Successfully ---")

except ImportError as e:
    print(f"❌ Missing package: {e}")
    exit(1)
except Exception as e:
    print(f"❌ Failed to initialize core services: {e}")
    exit(1)

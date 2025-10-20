import tiktoken
import chromadb
from chromadb.config import Settings
import google.generativeai as genai
from sentence_transformers import SentenceTransformer
from llama_parse import LlamaParse

from app.config import settings
from app.services.document_service import PDFProcessor, ExcelProcessor
from app.db.vector_store import VectorStoreManager
from app.db.document_store import DocumentStore

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
    document_store = DocumentStore()
    
    # This mimics the legacy global state for now. Will be replaced in Phase 2/3.
    upload_jobs: dict = {}
    # This is also legacy state. To be replaced.
    active_conversations: dict = {}

    print("--- Core Services Initialized Successfully ---")

except ImportError as e:
    print(f"❌ Missing package: {e}")
    exit(1)
except Exception as e:
    print(f"❌ Failed to initialize core services: {e}")
    exit(1)

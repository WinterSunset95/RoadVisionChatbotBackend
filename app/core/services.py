from google.generativeai.client import configure
from google.generativeai.generative_models import GenerativeModel
import tiktoken
import weaviate
import google.generativeai as genai
from sentence_transformers import SentenceTransformer
from llama_parse import LlamaParse

from app.config import settings
from app.modules.askai.models.document import UploadJob
from app.modules.askai.services.document_service import PDFProcessor, ExcelProcessor
from app.db.vector_store import VectorStoreManager

print("--- Initializing Core Services ---")

try:
    configure(api_key=settings.GOOGLE_API_KEY)
    llm_model = GenerativeModel("gemini-2.0-flash-exp")
    print("✅ Gemini 2.0 Flash configured")

    embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
    print("✅ SentenceTransformer loaded")

    try:
        weaviate_client = weaviate.connect_to_local()
        if not weaviate_client.is_ready():
            raise Exception("Weaviate is not ready")
        print("✅ Weaviate client connected")
    except Exception as e:
        print(f"❌ Could not connect to Weaviate: {e}")
        weaviate_client = None

    tokenizer = tiktoken.get_encoding("cl100k_base")

    pdf_processor = PDFProcessor(embedding_model, tokenizer)
    excel_processor = ExcelProcessor(embedding_model, tokenizer) 
    vector_store = VectorStoreManager(weaviate_client, embedding_model)
    
    # This mimics the legacy global state for now. Will be replaced in Phase 3 with Redis.
    # active_conversations and document_store are now handled by the database.

    print("--- Core Services Initialized Successfully ---")

except ImportError as e:
    print(f"❌ Missing package: {e}")
    exit(1)
except Exception as e:
    print(f"❌ Failed to initialize core services: {e}")
    exit(1)

"""
Service layer for initializing and managing Language Models and Embeddings.

This centralizes the setup for all AI-related models, ensuring they are
loaded only once and are available throughout the application.
"""
import os
import warnings
import google.generativeai as genai
from sentence_transformers import SentenceTransformer
import tiktoken
from ..core.config import settings as core_settings

# Suppress warnings for a cleaner console output
warnings.filterwarnings("ignore")
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Global variables for the models, to be initialized once.
model = None
embedding_model = None
tokenizer = None
pdf_processor = None # Will be initialized in document_service
excel_processor = None # Will be initialized in document_service

def initialize_llm():
    """
    Initializes and configures all the necessary AI models.
    This function is called once on application startup.
    """
    global model, embedding_model, tokenizer

    print("🤖 Initializing AI Models...")

    # Configure Gemini
    try:
        genai.configure(api_key=core_settings.GOOGLE_API_KEY)
        model = genai.GenerativeModel("gemini-2.0-flash-exp")
        print("✅ Gemini 2.0 Flash configured")
    except Exception as e:
        print(f"❌ Failed to configure Gemini: {e}")
        raise

    # Load Sentence Transformer for embeddings
    try:
        embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        print("✅ SentenceTransformer loaded")
    except Exception as e:
        print(f"❌ Failed to load SentenceTransformer: {e}")
        raise

    # Load tokenizer
    try:
        tokenizer = tiktoken.get_encoding("cl100k_base")
        print("✅ Tiktoken tokenizer loaded")
    except Exception as e:
        print(f"❌ Failed to load tokenizer: {e}")
        raise

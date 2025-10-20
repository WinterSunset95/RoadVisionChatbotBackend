"""
Main entry point to start the FastAPI application server.
"""
import uvicorn
from app.main import app
from app.core import config
from app.services import llm_service

if __name__ == "__main__":
    print("\n" + "="*70)
    print("🚀 PRODUCTION RAG BACKEND SERVER")
    print("="*70)
    print(f"📦 Vector DB: ChromaDB at {config.settings.CHROMA_PATH}")
    print(f"🤖 LLM: Gemini 2.0 Flash")
    print(f"🔍 OCR: LlamaParse {'✅' if llm_service.pdf_processor.has_llamaparse else '❌'}")
    print(f"📊 Embedding: SentenceTransformer")
    print(f"\n📝 Limits:")
    print(f"   - Max PDFs per chat: {config.settings.MAX_PDFS_PER_CHAT}")
    print(f"   - Max PDF size: {config.settings.MAX_PDF_SIZE_MB}MB")
    print("="*70 + "\n")

    print("🌐 Starting FastAPI server on http://0.0.0.0:5000")
    print("="*70 + "\n")

    # Uvicorn is a lightning-fast ASGI server, built on uvloop and httptools.
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=5000,
        log_level="info"
    )


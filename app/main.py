import os
import warnings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.router import api_router
from app.config import settings
from app.utils import ensure_directory_exists

# --- STABILITY FIXES ---
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["GRPC_VERBOSITY"] = "NONE"
os.environ["GRPC_CPP_VERBOSITY"] = "NONE"
os.environ["GLOG_minloglevel"] = "3"
warnings.filterwarnings("ignore")

# --- APP SETUP ---

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    app = FastAPI(
        title="RAG Chatbot API",
        description="API for the production RAG chatbot backend.",
        version="1.0.0",
    )

    # --- MIDDLEWARE ---
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"], # In production, restrict this to your frontend's domain
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- EVENT HANDLERS (STARTUP/SHUTDOWN) ---
    @app.on_event("startup")
    async def startup_event():
        print("--- Application Startup ---")
        
        # The services are initialized when the module is imported
        from app.core.global_stores import upload_jobs
        from app.core import services
        
        # Legacy file-based chat history loading is no longer needed.
        # Database connection is managed by the session dependency.
        print("--- Startup Complete ---")

    # --- ROUTERS ---
    app.include_router(api_router, prefix="/api")

    return app

app = create_app()

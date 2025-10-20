"""
Main application file that initializes the FastAPI app, includes the API router,
and runs startup tasks.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import routes as api_routes
from .services import llm_service, vector_store_service, document_service
from .db.base import Base, engine

# This command is now more appropriately placed here or managed by Alembic.
# For simplicity, we create tables on startup if they don't exist.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Chatbot Backend API",
    version="1.2.0",
    description="A refactored API for the RAG chatbot application using FastAPI and PostgreSQL."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    """Tasks to run when the application starts."""
    print("--- 🚀 Application Startup ---")
    llm_service.initialize_llm()
    vector_store_service.initialize_vector_store()
    document_service.initialize_processors()
    # No longer need to load from JSON
    print("✅ Application startup complete.")

app.include_router(api_routes.router, prefix="/api", tags=["Chat API"])

@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Welcome to the Chatbot API! Visit /docs for documentation."}

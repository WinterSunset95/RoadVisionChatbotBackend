import os
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# --- FastAPI APP INITIALIZATION ---

app = FastAPI(
    title="RAG Chatbot API",
    description="API for the production RAG chatbot backend.",
    version="1.0.0",
)

# --- MIDDLEWARE ---

# Configure CORS to allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to your frontend's domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- UTILITIES ---

def get_consistent_timestamp():
    """Return ISO format timestamp"""
    return datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%fZ')

# --- MODELS (Pydantic Schemas) ---

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    # This will be populated later
    # llamaparse: str

# --- API ENDPOINTS ---

@app.get("/api/health", response_model=HealthResponse, tags=["Health"])
def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "timestamp": get_consistent_timestamp(),
        # "llamaparse": "available" # TODO: Add logic to check for LlamaParse
    }

# --- STARTUP ---

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*70)
    print("🚀 DEVELOPMENT RAG BACKEND SERVER (FastAPI)")
    print("="*70)
    
    # In a real app, you'd load config and initialize services here
    
    print("🌐 Starting Uvicorn server on http://0.0.0.0:5000")
    print("📚 API docs available at http://0.0.0.0:5000/docs")
    print("="*70 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=5000)

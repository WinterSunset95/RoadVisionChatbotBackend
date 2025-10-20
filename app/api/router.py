from fastapi import APIRouter
from app.api.endpoints import health, chats, documents

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(chats.router)
api_router.include_router(documents.router)

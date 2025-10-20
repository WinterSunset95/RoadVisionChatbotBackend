from typing import List
from fastapi import APIRouter, HTTPException, Path, Body, status
from app.models.chat import ChatMetadata, Message, NewMessageRequest, NewMessageResponse, RenameChatRequest
from app.services import chat_service, rag_service

router = APIRouter()

@router.get("/chats", response_model=List[ChatMetadata], tags=["Chats"])
def get_chats():
    """Get all chats, sorted by last updated"""
    return chat_service.get_all_chats()

@router.post("/chats", response_model=ChatMetadata, status_code=status.HTTP_201_CREATED, tags=["Chats"])
def create_chat():
    """Create a new chat session"""
    return chat_service.create_new_chat()

@router.get("/chats/{chat_id}", response_model=List[Message], tags=["Chats"])
def get_chat(chat_id: str = Path(..., description="The ID of the chat to retrieve")):
    """Get all messages for a specific chat"""
    return chat_service.get_chat_messages(chat_id)

@router.delete("/chats/{chat_id}", status_code=status.HTTP_200_OK, tags=["Chats"])
def delete_chat(chat_id: str = Path(..., description="The ID of the chat to delete")):
    """Delete a chat session and its associated data"""
    success = chat_service.delete_chat_by_id(chat_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")
    return {"message": "Chat deleted successfully"}

@router.put("/chats/{chat_id}/rename", status_code=status.HTTP_200_OK, tags=["Chats"])
def rename_chat(
    chat_id: str = Path(..., description="The ID of the chat to rename"),
    payload: RenameChatRequest = Body(...)
):
    """Rename a chat session"""
    if not payload.title or not payload.title.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Title cannot be empty")
    
    success = chat_service.rename_chat_by_id(chat_id, payload.title.strip())
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")
    return {"message": "Chat renamed successfully"}

@router.post("/chats/{chat_id}/messages", response_model=NewMessageResponse, tags=["Chats"])
def send_message(
    chat_id: str = Path(..., description="The ID of the chat to send a message to"),
    payload: NewMessageRequest = Body(...)
):
    """Send a message to a chat and get a RAG-based response"""
    if not payload.message or not payload.message.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Message cannot be empty")
    
    return rag_service.send_message_to_chat(chat_id, payload.message.strip())

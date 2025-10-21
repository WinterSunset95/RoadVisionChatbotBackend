from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict

class ChatMetadata(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    title: str
    created_at: str
    updated_at: str
    message_count: int
    has_pdf: bool
    pdf_count: int
    pdf_list: List[dict] = []

class Message(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    text: str
    sender: str # 'user' or 'bot'
    timestamp: str

class NewMessageRequest(BaseModel):
    message: str

class Source(BaseModel):
    id: int
    source: str
    location: str
    doc_type: str
    content_type: str
    content: str
    full_content: str
    page: Optional[str] = None

class NewMessageResponse(BaseModel):
    reply: str
    sources: List[Source]
    message_count: int

class RenameChatRequest(BaseModel):
    title: str

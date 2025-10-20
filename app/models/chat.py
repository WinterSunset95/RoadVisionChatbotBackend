from typing import List, Optional
from pydantic import BaseModel

class ChatMetadata(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int
    has_pdf: bool
    pdf_count: int
    pdf_list: List[dict] = []

class Message(BaseModel):
    id: str
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

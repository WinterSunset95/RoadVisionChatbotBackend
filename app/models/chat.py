from typing import List, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, ConfigDict, Field
from .document import EmbeddedDocument

# --- Models for data stored in MongoDB ---

class EmbeddedMessage(BaseModel):
    """Represents a message embedded in a Chat document."""
    id: UUID = Field(default_factory=uuid4)
    sender: str  # 'user' or 'bot'
    text: str
    timestamp: str

class Chat(BaseModel):
    """The main Chat document model for MongoDB."""
    id: UUID = Field(default_factory=uuid4, alias="_id")
    title: str
    created_at: str
    updated_at: str
    documents: List[EmbeddedDocument] = []
    messages: List[EmbeddedMessage] = []

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={UUID: str},
    )

# --- Models for API Request/Response (for backward compatibility) ---

class Message(BaseModel):
    """Model for API responses for a single chat's messages."""
    id: str
    text: str
    sender: str
    timestamp: str

class ChatMetadata(BaseModel):
    """Model for the list of chats API response."""
    id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int
    has_pdf: bool
    pdf_count: int
    pdf_list: List[dict] = []

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

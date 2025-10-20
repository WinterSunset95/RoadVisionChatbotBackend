"""
Pydantic Schemas for API Data Validation and Serialization.
This is the API contract for the frontend.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Any
from datetime import datetime

class DocumentMetadata(BaseModel):
    name: str
    upload_time: str
    chunks_added: int
    status: str

class ChatResponse(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int
    has_pdf: bool
    pdf_count: int
    pdf_list: List[DocumentMetadata]

class MessageResponse(BaseModel):
    id: str
    text: str
    sender: str
    timestamp: datetime
    hasContext: bool = False
    sourceReferences: List[Any] = []

class SendMessageRequest(BaseModel):
    message: str

class BotReply(BaseModel):
    reply: str
    sources: List[Any]
    message_count: int

class RenameChatRequest(BaseModel):
    title: str

class PdfInfo(BaseModel):
    name: str
    chunks: int
    status: str

class ChatPdfsResponse(BaseModel):
    pdfs: List[PdfInfo]
    total_pdfs: int
    chat_id: str

class UploadAcceptedResponse(BaseModel):
    message: str
    job_id: str
    processing: bool

class UploadStatusResponse(BaseModel):
    job_id: str
    status: str
    started_at: datetime
    chat_id: Optional[str] = None
    filename: Optional[str] = None
    finished_at: Optional[datetime] = None
    chunks_added: Optional[int] = None
    error: Optional[str] = None



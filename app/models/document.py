from typing import List, Optional, Any
from uuid import UUID, uuid4
from pydantic import BaseModel, ConfigDict, Field


class EmbeddedDocument(BaseModel):
    """
    Represents a document embedded within a Chat document in MongoDB.
    """
    id: UUID = Field(default_factory=uuid4)
    filename: str
    doc_type: str = "pdf"
    file_hash: str
    file_size: int
    chunks_count: int
    status: str = "active"
    uploaded_at: str
    processing_stats: Optional[dict[str, Any]] = None

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={UUID: str},
    )


class DocumentMetadata(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    name: str
    chunks: int
    status: str

class ProcessingJob(BaseModel):
    name: str
    job_id: str
    status: str

class ChatDocumentsResponse(BaseModel):
    pdfs: List[DocumentMetadata]
    xlsx: List[DocumentMetadata]
    processing: List[ProcessingJob]
    total_docs: int
    chat_id: str

class UploadAcceptedResponse(BaseModel):
    message: str
    job_id: str
    processing: bool

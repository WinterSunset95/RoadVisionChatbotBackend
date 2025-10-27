from enum import Enum
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

class ProcessingStatus(Enum):
    QUEUED = "queued"
    DOWNLOADING = "downloading"
    PROCESSING = "processing"
    FINISHED = "finished"
    FAILED = "failed"

class ProcessingStage(Enum):
    NOT_PROCESSING = "not_processing"
    EXTRACTING_CONTENT = "extracting_content"
    ADDING_TO_VECTOR_STORE = "adding_to_vector_store"
    SAVING_METADATA = "saving_metadata"

class UploadJob(BaseModel):
    job_id: str
    filename: str
    chat_id: str
    status: ProcessingStatus
    stage: ProcessingStage
    progress: float
    finished_at: str
    chunks_added: int
    error: Optional[str]

class ProcessingJob(BaseModel):
    name: str
    job_id: str
    status: ProcessingStatus
    stage: ProcessingStage
    progress: float

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

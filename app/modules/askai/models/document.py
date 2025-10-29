from enum import Enum
from typing import List, Optional, Any
from uuid import UUID, uuid4
from pydantic import Field
from app.db.base import MongoDBModel


class EmbeddedDocument(MongoDBModel):
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
    LLAMA_LOADING = "llama_loading"
    PYMUPDF_LOADING = "pymupdf_loading"
    TESSERACT_LOADING = "tesseract_loading"
    EXTRACTING_CONTENT = "extracting_content"
    EXTRACTING_TABLES = "extracting_tables"
    CREATING_CHUNKS = "creating_chunks"
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

class DriveFile(BaseModel):
    # Some drive related metadata
    id: str
    name: str
    mime_type: str = Field(..., alias="mimeType")
    size: Optional[str] = None

class DriveFolder(BaseModel):
    id: str
    files: List[DriveFile]
    subfolders: List['DriveFolder']

DriveFolder.model_rebuild()

class ChatDocumentsResponse(BaseModel):
    pdfs: List[DocumentMetadata]
    xlsx: List[DocumentMetadata]
    processing: List[ProcessingJob]
    drive_folders: List[DriveFolder]
    total_docs: int
    chat_id: str

class UploadAcceptedResponse(BaseModel):
    message: str
    job_id: str
    processing: bool

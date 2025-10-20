from typing import List
from pydantic import BaseModel

class DocumentMetadata(BaseModel):
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

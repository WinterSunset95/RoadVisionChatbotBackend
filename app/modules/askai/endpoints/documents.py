from typing import List
import uuid
import tempfile
import os
import stat
import asyncio
import json
from fastapi import APIRouter, HTTPException, Path, UploadFile, File, BackgroundTasks, status, Depends, Request
from sse_starlette.sse import EventSourceResponse
from pymongo.database import Database
from app.modules.askai.models.document import AddDriveRequest, ChatDocumentsResponse, DriveFolder, ProcessingJob, ProcessingStage, ProcessingStatus, UploadAcceptedResponse, DocumentMetadata, UploadJob
from app.modules.askai.models.chat import Chat
from app.core.services import vector_store
from app.core.global_stores import upload_jobs
from app.db.mongo_client import get_database
from app.config import settings
from app.modules.askai.services import drive_service
from app.modules.askai.services.document_processing_service import process_uploaded_pdf

router = APIRouter()

@router.post("/chats/{chat_id}/upload-pdf", response_model=UploadAcceptedResponse, status_code=status.HTTP_202_ACCEPTED, tags=["Documents"])
async def upload_pdf(
    chat_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: Database = Depends(get_database),
    pdf: UploadFile = File(..., description="The PDF file to upload", alias="pdf")
):
    """Upload a PDF for RAG processing. This is an asynchronous operation."""
    if not (pdf.filename or "unknown").lower().endswith(".pdf"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File must be a PDF")

    chat_doc = db["chats"].find_one({"_id": chat_id})
    if not chat_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")
    
    chat = Chat.model_validate(chat_doc)

    if len(chat.documents) >= settings.MAX_PDFS_PER_CHAT:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Maximum {settings.MAX_PDFS_PER_CHAT} PDFs per chat")

    if any(doc.filename == pdf.filename for doc in chat.documents):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"PDF '{pdf.filename}' already uploaded")

    # Save to a temporary file
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            content = await pdf.read()
            if len(content) > settings.MAX_PDF_SIZE_MB * 1024 * 1024:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"File too large. Max: {settings.MAX_PDF_SIZE_MB}MB")
            
            tmp.write(content)
            temp_path = tmp.name
        
        os.chmod(temp_path, stat.S_IRUSR | stat.S_IWUSR)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Could not save uploaded file: {e}")

    # Start background processing
    job_id = str(uuid.uuid4())
    upload_jobs[job_id] = UploadJob(
        job_id = job_id,
        status=ProcessingStatus.QUEUED,
        chat_id=str(chat_id),
        filename=pdf.filename or "unknown-file.pdf",
        progress=0,
        stage=ProcessingStage.NOT_PROCESSING,
        finished_at="",
        chunks_added=0,
        error=None
    )
    background_tasks.add_task(process_uploaded_pdf, temp_path, str(chat_id), pdf.filename or "unknown-file.pdf", job_id)

    return {"message": "Upload accepted", "job_id": job_id, "processing": True}

@router.post("/chats/{chat_id}/add-drive", response_model=DriveFolder, tags=["Documents"])
def add_drive_folder(
    chat_id: uuid.UUID,
    payload: AddDriveRequest,
    db: Database = Depends(get_database)
):
    """
    Scans a public Google Drive folder and adds its file structure to the chat
    without downloading the files.
    """
    chat_doc = db["chats"].find_one({"_id": chat_id})
    if not chat_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")
    
    try:
        folder_structure = drive_service.add_drive_folder_to_chat(db, chat_id, payload.driveUrl)
        return folder_structure
    except (ValueError, Exception) as e:
        # Catches invalid URLs from service logic and other potential errors.
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/upload-status/{job_id}", tags=["Documents"])
def get_upload_status(job_id: str = Path(..., description="The ID of the upload job")):
    """Get the status of an asynchronous upload job"""
    status = upload_jobs.get(job_id)
    if not status:
        raise HTTPException(status_code=404, detail="Job not found")
    return status

def _get_chat_docs_data(chat_id: uuid.UUID, db: Database) -> dict:
    """Helper function to fetch and structure document data for a chat."""
    chat_doc = db["chats"].find_one({"_id": chat_id})
    if not chat_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")

    chat = Chat.model_validate(chat_doc)
    
    pdfs = [DocumentMetadata(name=doc.filename, chunks=doc.chunks_count, status=doc.status) for doc in chat.documents if doc.doc_type == 'pdf']
    excel = [DocumentMetadata(name=doc.filename, chunks=doc.chunks_count, status=doc.status) for doc in chat.documents if doc.doc_type == 'excel']

    processing_jobs: List[ProcessingJob] = []
    for jid, job in upload_jobs.items():
        if job.chat_id == str(chat_id):
            processing_job = ProcessingJob(name=job.filename, job_id=jid, status=job.status, stage=job.stage, progress=job.progress)
            processing_jobs.append(processing_job)
    
    response_data = ChatDocumentsResponse(
        pdfs=pdfs,
        xlsx=excel,
        processing=processing_jobs,
        drive_folders=chat.drive_folders,
        total_docs=len(pdfs) + len(excel) + len(processing_jobs),
        chat_id=str(chat_id)
    )
    return response_data.model_dump()

@router.get("/chats/{chat_id}/docs", response_model=ChatDocumentsResponse, tags=["Documents"])
def get_chat_docs(chat_id: uuid.UUID, db: Database = Depends(get_database)):
    """Get all active and processing documents for a specific chat"""
    return _get_chat_docs_data(chat_id, db)

@router.delete("/chats/{chat_id}/pdfs/{pdf_name}", tags=["Documents"])
def delete_chat_pdf(chat_id: uuid.UUID, pdf_name: str, db: Database = Depends(get_database)):
    """Delete a specific PDF from a chat"""
    chat_doc = db["chats"].find_one({"_id": chat_id})
    if not chat_doc:
        raise HTTPException(status_code=404, detail="Chat not found")

    doc_to_delete = next((doc for doc in chat_doc.get("documents", []) if doc["filename"] == pdf_name), None)
    if not doc_to_delete:
        raise HTTPException(status_code=404, detail=f"PDF '{pdf_name}' not found in this chat")

    db["chats"].update_one(
        {"_id": chat_id},
        {"$pull": {"documents": {"filename": pdf_name}}}
    )

    # If this was the last document, delete the whole vector collection.
    if len(chat_doc.get("documents", [])) == 1:
        vector_store.delete_collection(str(chat_id))
    
    # TODO: Implement granular vector deletion if needed.
    
    return {"message": "PDF removed successfully", "chat_id": str(chat_id), "pdf_name": pdf_name}

# --- Compatibility Endpoints ---

@router.get("/chats/{chat_id}/pdfs", tags=["Documents", "Compatibility"], summary="Get Chat PDFs (Legacy)")
def get_chat_pdfs_legacy(chat_id: uuid.UUID, db: Database = Depends(get_database)):
    """(Legacy) Get PDF information for a chat."""
    chat_doc = db["chats"].find_one({"_id": chat_id})
    if not chat_doc:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    chat = Chat.model_validate(chat_doc)
    pdf_list_metadata = [
        {
            "name": doc.filename,
            "chunks_added": doc.chunks_count,
            "status": doc.status,
            "upload_time": doc.uploaded_at
        } for doc in chat.documents
    ]
    return {"pdfs": pdf_list_metadata, "total_pdfs": len(pdf_list_metadata), "chat_id": str(chat_id)}

@router.get("/pdfs", tags=["Documents", "Compatibility"], summary="Get All PDFs (Legacy)")
def get_all_pdfs_legacy(db: Database = Depends(get_database)):
    """(Legacy) Get all PDFs across all chats."""
    all_pdfs = []
    chat_docs = db["chats"].find()
    for chat_doc in chat_docs:
        chat = Chat.model_validate(chat_doc)
        for doc in chat.documents:
            all_pdfs.append({
                "chat_id": str(chat.id), "chat_title": chat.title,
                "name": doc.filename, "chunks": doc.chunks_count,
                "status": doc.status, "uploaded_at": doc.uploaded_at
            })
    return {"pdfs": all_pdfs, "total_pdfs": len(all_pdfs)}

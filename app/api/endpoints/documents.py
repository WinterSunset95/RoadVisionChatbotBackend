import uuid
import tempfile
import os
import stat
from fastapi import APIRouter, HTTPException, Path, UploadFile, File, BackgroundTasks, status, Depends
from sqlalchemy.orm import Session
from app.models.document import ChatDocumentsResponse, UploadAcceptedResponse, DocumentMetadata
from app.core.services import upload_jobs, vector_store
from app.db import crud
from app.db.session import get_db
from app.config import settings
from app.services.document_processing_service import process_uploaded_pdf

router = APIRouter()

@router.post("/chats/{chat_id}/upload-pdf", response_model=UploadAcceptedResponse, status_code=status.HTTP_202_ACCEPTED, tags=["Documents"])
async def upload_pdf(
    chat_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    pdf: UploadFile = File(..., description="The PDF file to upload", alias="pdf")
):
    """Upload a PDF for RAG processing. This is an asynchronous operation."""
    if not pdf.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File must be a PDF")

    chat = crud.get_chat(db, chat_id)
    if not chat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")

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
    upload_jobs[job_id] = {
        "job_id": job_id, "status": "queued", "chat_id": str(chat_id), "filename": pdf.filename
    }
    background_tasks.add_task(process_uploaded_pdf, temp_path, str(chat_id), pdf.filename, job_id)

    return {"message": "Upload accepted", "job_id": job_id, "processing": True}

@router.get("/upload-status/{job_id}", tags=["Documents"])
def get_upload_status(job_id: str = Path(..., description="The ID of the upload job")):
    """Get the status of an asynchronous upload job"""
    status = upload_jobs.get(job_id)
    if not status:
        raise HTTPException(status_code=404, detail="Job not found")
    return status

@router.get("/chats/{chat_id}/docs", response_model=ChatDocumentsResponse, tags=["Documents"])
def get_chat_docs(chat_id: uuid.UUID, db: Session = Depends(get_db)):
    """Get all active and processing documents for a specific chat"""
    completed_docs = crud.get_chat_documents(db, chat_id)
    pdfs = [DocumentMetadata(name=doc.filename, chunks=doc.chunks_count, status=doc.status) for doc in completed_docs if doc.doc_type == 'pdf']
    excel = [DocumentMetadata(name=doc.filename, chunks=doc.chunks_count, status=doc.status) for doc in completed_docs if doc.doc_type == 'excel']

    processing_jobs = [
        {"name": job.get("filename"), "job_id": jid, "status": job.get("status")}
        for jid, job in upload_jobs.items()
        if job.get("chat_id") == str(chat_id) and job.get("status") in ["queued", "processing"]
    ]

    return {
        "pdfs": pdfs, "xlsx": excel, "processing": processing_jobs,
        "total_docs": len(pdfs) + len(excel) + len(processing_jobs),
        "chat_id": str(chat_id)
    }

@router.delete("/chats/{chat_id}/pdfs/{pdf_name}", tags=["Documents"])
def delete_chat_pdf(chat_id: uuid.UUID, pdf_name: str, db: Session = Depends(get_db)):
    """Delete a specific PDF from a chat"""
    chat = crud.get_chat(db, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    doc_to_delete = next((doc for doc in chat.documents if doc.filename == pdf_name), None)
    if not doc_to_delete:
        raise HTTPException(status_code=404, detail=f"PDF '{pdf_name}' not found in this chat")
    
    crud.delete_document(db, doc_to_delete)
    
    # If this was the last document, delete the whole vector collection.
    if len(chat.documents) == 0:
        vector_store.delete_collection(str(chat_id))
    
    # TODO: Implement granular vector deletion if needed.
    
    return {"message": "PDF removed successfully", "chat_id": str(chat_id), "pdf_name": pdf_name}

# --- Compatibility Endpoints ---

@router.get("/chats/{chat_id}/pdfs", tags=["Documents", "Compatibility"], summary="Get Chat PDFs (Legacy)")
def get_chat_pdfs_legacy(chat_id: uuid.UUID, db: Session = Depends(get_db)):
    """(Legacy) Get PDF information for a chat."""
    chat = crud.get_chat(db, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    pdf_list_metadata = [
        {
            "name": doc.filename,
            "chunks_added": doc.chunks_count,
            "status": doc.status,
            "upload_time": doc.uploaded_at.isoformat()
        } for doc in chat.documents
    ]
    return {"pdfs": pdf_list_metadata, "total_pdfs": len(pdf_list_metadata), "chat_id": str(chat_id)}

@router.get("/pdfs", tags=["Documents", "Compatibility"], summary="Get All PDFs (Legacy)")
def get_all_pdfs_legacy(db: Session = Depends(get_db)):
    """(Legacy) Get all PDFs across all chats."""
    all_pdfs = []
    chats = crud.get_chats(db)
    for chat in chats:
        for doc in chat.documents:
            all_pdfs.append({
                "chat_id": str(chat.id), "chat_title": chat.title,
                "name": doc.filename, "chunks": doc.chunks_count,
                "status": doc.status, "uploaded_at": doc.uploaded_at.isoformat()
            })
    return {"pdfs": all_pdfs, "total_pdfs": len(all_pdfs)}

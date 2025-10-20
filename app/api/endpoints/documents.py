import uuid
import tempfile
import os
import stat
from fastapi import APIRouter, HTTPException, Path, UploadFile, File, BackgroundTasks, status
from app.models.document import ChatDocumentsResponse, UploadAcceptedResponse
from app.core.services import upload_jobs, document_store, vector_store
from app.db import file_store
from app.config import settings
from app.services.document_processing_service import process_uploaded_pdf
from app.utils import get_consistent_timestamp

router = APIRouter()

@router.post("/chats/{chat_id}/upload-pdf", response_model=UploadAcceptedResponse, status_code=status.HTTP_202_ACCEPTED, tags=["Documents"])
async def upload_pdf(
    background_tasks: BackgroundTasks,
    chat_id: str = Path(..., description="The ID of the chat to upload the document to"),
    pdf: UploadFile = File(..., description="The PDF file to upload", alias="pdf")
):
    """Upload a PDF for RAG processing. This is an asynchronous operation."""
    if not pdf.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File must be a PDF")

    chat_history = file_store.load_chat_history()
    chat = next((c for c in chat_history if c["id"] == chat_id), None)
    if not chat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")

    pdf_list = chat.get("pdf_list", [])
    if len(pdf_list) >= settings.MAX_PDFS_PER_CHAT:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Maximum {settings.MAX_PDFS_PER_CHAT} PDFs per chat")

    if any(p.get("name") == pdf.filename for p in pdf_list):
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
        "job_id": job_id, "status": "queued", "chat_id": chat_id, "filename": pdf.filename
    }
    background_tasks.add_task(process_uploaded_pdf, temp_path, chat_id, pdf.filename, job_id)

    return {"message": "Upload accepted", "job_id": job_id, "processing": True}

@router.get("/upload-status/{job_id}", tags=["Documents"])
def get_upload_status(job_id: str = Path(..., description="The ID of the upload job")):
    """Get the status of an asynchronous upload job"""
    status = upload_jobs.get(job_id)
    if not status:
        raise HTTPException(status_code=404, detail="Job not found")
    return status

@router.get("/chats/{chat_id}/docs", response_model=ChatDocumentsResponse, tags=["Documents"])
def get_chat_docs(chat_id: str = Path(..., description="The ID of the chat")):
    """Get all active and processing documents for a specific chat"""
    completed_docs = document_store.get_chat_documents(chat_id)
    pdfs, excel = [], []
    for doc in completed_docs:
        doc_info = {"name": doc.get("filename", "Unknown"), "chunks": doc.get("chunks_count", 0), "status": "active"}
        if doc.get("doc_type") == "pdf":
            pdfs.append(doc_info)
        elif doc.get("doc_type") == "excel":
            excel.append(doc_info)

    processing_jobs = [
        {"name": job.get("filename"), "job_id": jid, "status": job.get("status")}
        for jid, job in upload_jobs.items()
        if job.get("chat_id") == chat_id and job.get("status") in ["queued", "processing"]
    ]

    return {
        "pdfs": pdfs, "xlsx": excel, "processing": processing_jobs,
        "total_docs": len(pdfs) + len(excel) + len(processing_jobs),
        "chat_id": chat_id
    }

@router.delete("/chats/{chat_id}/pdfs/{pdf_name}", tags=["Documents"])
def delete_chat_pdf(
    chat_id: str = Path(..., description="The ID of the chat"),
    pdf_name: str = Path(..., description="The filename of the PDF to delete")
):
    """Delete a specific PDF from a chat"""
    chat_history = file_store.load_chat_history()
    chat = next((c for c in chat_history if c["id"] == chat_id), None)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    pdf_list = chat.get("pdf_list", [])
    pdf_to_remove = next((p for p in pdf_list if p.get("name") == pdf_name), None)
    if not pdf_to_remove:
        raise HTTPException(status_code=404, detail=f"PDF '{pdf_name}' not found")
    
    chat["pdf_list"] = [p for p in pdf_list if p.get("name") != pdf_name]
    chat["pdf_count"] = len(chat["pdf_list"])
    chat["has_pdf"] = len(chat["pdf_list"]) > 0
    chat["updated_at"] = get_consistent_timestamp()

    if not chat["pdf_list"]:
        vector_store.delete_collection(chat_id)
    
    # TODO: Need more granular deletion from vector store if other PDFs remain.
    # For now, we only clear the whole collection if it's the last PDF.
    
    file_store.save_chat_history(chat_history)
    return {"message": "PDF removed successfully", "chat_id": chat_id, "pdf_name": pdf_name}

# --- Compatibility Endpoints ---

@router.get("/chats/{chat_id}/pdfs", tags=["Documents", "Compatibility"], summary="Get Chat PDFs (Legacy)")
def get_chat_pdfs_legacy(chat_id: str = Path(..., description="The ID of the chat")):
    """(Legacy) Get PDF information for a chat."""
    chat_history = file_store.load_chat_history()
    chat = next((c for c in chat_history if c["id"] == chat_id), None)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    pdf_list_metadata = chat.get("pdf_list", [])
    return {"pdfs": pdf_list_metadata, "total_pdfs": len(pdf_list_metadata), "chat_id": chat_id}

@router.get("/pdfs", tags=["Documents", "Compatibility"], summary="Get All PDFs (Legacy)")
def get_all_pdfs_legacy():
    """(Legacy) Get all PDFs across all chats."""
    all_pdfs = []
    chat_history = file_store.load_chat_history()
    for chat in chat_history:
        for pdf_meta in chat.get("pdf_list", []):
            all_pdfs.append({
                "chat_id": chat["id"], "chat_title": chat.get("title"),
                **pdf_meta
            })
    return {"pdfs": all_pdfs, "total_pdfs": len(all_pdfs)}

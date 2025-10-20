"""
Service layer for handling document processing and uploads.
"""
import os
import tempfile
import threading
import traceback
import uuid
from typing import Any, Dict, List, Optional
from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..core import config
from ..db import crud
from ..utils import helpers
from . import llm_service, vector_store_service

# ... (Full PDFProcessor and ExcelProcessor classes remain here) ...

# Global variables for processors and job tracking
# ...

def _background_process_pdf(job_id: str, chat_id: str, temp_path: str, filename: str, file_hash: str, file_size: int):
    # ... (Implementation remains the same, but it will now use crud functions via db session if needed) ...
    # CRITICAL CHANGE: It no longer modifies chat_history directly. It must now update the DB.
    # This part requires passing a DB session or making a separate request, which is complex with threads.
    # For now, we'll assume it updates a Pydantic model passed to it, and the caller saves it.
    
    # Let's simplify for now: the main `handle_pdf_upload` will update the DB *after* the thread is done.
    # This isn't ideal for long processes but avoids complex session management in threads.
    # A better solution would involve Celery.

    status = upload_jobs[job_id]
    status.update({"status": "processing"})
    
    try:
        # DB Interaction needs to be handled carefully in threads.
        # A simple approach is to create a new session inside the thread.
        from ..db.base import SessionLocal
        db = SessionLocal()
        
        doc_id = str(uuid.uuid4())
        chunks, stats = pdf_processor.process_pdf(temp_path, doc_id, filename)
        
        if not chunks:
            raise Exception("No content could be extracted.")
        
        collection = vector_store_service.vector_store_manager.get_or_create_collection(chat_id)
        added_count = vector_store_service.vector_store_manager.add_chunks(collection, chunks)
        
        chat = crud.get_chat(db, chat_id)
        if chat:
            new_pdf_meta = {"name": filename, "upload_time": helpers.get_consistent_timestamp(), "chunks_added": added_count, "status": "active"}
            
            # Safely update the JSONB field
            current_pdf_list = chat.pdf_list if chat.pdf_list else []
            current_pdf_list.append(new_pdf_meta)
            
            crud.update_chat_metadata(db, chat, pdf_list=current_pdf_list)

        status.update({"status": "done", "finished_at": helpers.get_consistent_timestamp(), "chunks_added": added_count})
        
        db.close()

    except Exception as e:
        status.update({"status": "error", "error": str(e), "finished_at": helpers.get_consistent_timestamp()})
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def handle_pdf_upload(db: Session, chat_id: str, pdf_file: UploadFile):
    # ... (Validation logic remains the same) ...

    # The rest of the logic for saving file and starting thread remains the same
    # ...

def delete_pdf_from_chat(db: Session, chat_id: str, pdf_name: str):
    chat = crud.get_chat(db, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    pdf_list = chat.pdf_list or []
    if not any(p.get("name") == pdf_name for p in pdf_list):
        raise HTTPException(status_code=404, detail=f"PDF '{pdf_name}' not found")

    updated_pdf_list = [p for p in pdf_list if p.get("name") != pdf_name]
    crud.update_chat_metadata(db, chat, pdf_list=updated_pdf_list)

    if not updated_pdf_list:
        vector_store_service.vector_store_manager.delete_collection(chat_id)



import os
import uuid
import traceback
import tempfile
import stat

from app.core.services import (
    pdf_processor, vector_store, document_store, upload_jobs
)
from app.db import file_store
from app.utils import get_consistent_timestamp, get_file_hash
from app.config import settings

def process_uploaded_pdf(temp_path: str, chat_id: str, filename: str, job_id: str):
    """
    Background task to process a PDF file.
    This function contains the core logic from the original `process_pdf` thread.
    """
    status = upload_jobs.get(job_id, {})
    status.update({
        "status": "processing",
        "started_at": get_consistent_timestamp()
    })

    try:
        # 1. Process PDF to get chunks and stats
        doc_id = str(uuid.uuid4())
        chunks, stats = pdf_processor.process_pdf(temp_path, doc_id, filename)
        
        if not chunks:
            raise Exception("No content extracted from PDF")
        
        # 2. Add chunks to vector store
        collection = vector_store.get_or_create_collection(chat_id)
        added_count = vector_store.add_chunks(collection, chunks)
        
        # 3. Save document metadata
        file_size = os.path.getsize(temp_path)
        file_hash = get_file_hash(temp_path)
        
        doc_metadata = {
            "filename": filename, "doc_type": "pdf", "file_hash": file_hash,
            "file_size": file_size, "chunks_count": added_count, **stats
        }
        document_store.add_document(chat_id, doc_metadata)
        
        # 4. Update chat history
        chat_history = file_store.load_chat_history()
        for chat in chat_history:
            if chat["id"] == chat_id:
                if "pdf_list" not in chat: chat["pdf_list"] = []
                chat["pdf_list"].append({
                    "name": filename,
                    "upload_time": get_consistent_timestamp(),
                    "chunks_added": added_count,
                    "status": "active"
                })
                chat["has_pdf"] = True
                chat["pdf_count"] = len(chat["pdf_list"])
                chat["updated_at"] = get_consistent_timestamp()
                break
        file_store.save_chat_history(chat_history)
        
        # 5. Update job status to 'done'
        status.update({
            "status": "done",
            "finished_at": get_consistent_timestamp(),
            "chunks_added": added_count
        })
        print(f"✅ PDF {filename} processed successfully for job {job_id}")

    except Exception as e:
        error_msg = str(e)
        print(f"❌ Processing error for job {job_id}: {error_msg}")
        traceback.print_exc()
        status.update({
            "status": "error", "error": error_msg,
            "finished_at": get_consistent_timestamp()
        })
    
    finally:
        # 6. Clean up temporary file
        try:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        except Exception as e:
            print(f"⚠️  Cleanup error for job {job_id}: {e}")

import os
from uuid import UUID, uuid4
import traceback

from app.core.services import pdf_processor, vector_store, upload_jobs
from app.db.mongo_client import MongoClientConnection
from app.models.document import EmbeddedDocument
from app.utils import get_consistent_timestamp, get_file_hash
from app.config import settings

def process_uploaded_pdf(temp_path: str, chat_id_str: str, filename: str, job_id: str):
    """
    Background task to process a PDF file.
    This function gets its own database connection.
    """
    status = upload_jobs.get(job_id, {})
    status.update({"status": "processing", "started_at": get_consistent_timestamp()})

    client_conn = None
    try:
        client_conn = MongoClientConnection(settings.MONGODB_URL)
        db = client_conn.get_database()
        chat_id = UUID(chat_id_str)

        # 1. Process PDF to get chunks and stats
        doc_id_str = str(uuid4())
        chunks, stats = pdf_processor.process_pdf(temp_path, doc_id_str, filename)
        
        if not chunks:
            raise Exception("No content extracted from PDF")
        
        # 2. Add chunks to vector store
        collection = vector_store.get_or_create_collection(chat_id_str)
        added_count = vector_store.add_chunks(collection, chunks)
        
        # 3. Save document metadata to DB
        now = get_consistent_timestamp()
        new_document = EmbeddedDocument(
            filename=filename,
            file_hash=get_file_hash(temp_path),
            file_size=os.path.getsize(temp_path),
            chunks_count=added_count,
            uploaded_at=now,
            processing_stats=stats
        )
        
        db["chats"].update_one(
            {"_id": chat_id},
            {
                "$push": {"documents": new_document.model_dump()},
                "$set": {"updated_at": now}
            }
        )
        
        # 4. Update job status to 'done'
        status.update({
            "status": "done",
            "finished_at": now,
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
        if client_conn and client_conn.client:
            client_conn.client.close()
        # 6. Clean up temporary file
        try:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        except Exception as e:
            print(f"⚠️  Cleanup error for job {job_id}: {e}")

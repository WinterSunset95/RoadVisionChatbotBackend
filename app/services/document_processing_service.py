import os
from uuid import UUID, uuid4
import traceback

from app.core.services import pdf_processor, vector_store
from app.core.global_stores import upload_jobs
from app.db.mongo_client import MongoClientConnection
from app.models.document import EmbeddedDocument, ProcessingStage, ProcessingStatus, UploadJob
from app.utils import get_consistent_timestamp, get_file_hash
from app.config import settings

def process_uploaded_pdf(temp_path: str, chat_id_str: str, filename: str, job_id: str):
    """
    Background task to process a PDF file.
    This function gets its own database connection.
    """
    upload_job = upload_jobs.get(job_id, {})
    if type(upload_job) is not UploadJob:
        return

    upload_job.status = ProcessingStatus.PROCESSING
    upload_job.stage = ProcessingStage.EXTRACTING_CONTENT
    upload_job.progress = 0
    # status.update({"status": "processing", "started_at": get_consistent_timestamp()})

    client_conn = None
    try:
        client_conn = MongoClientConnection(settings.MONGO_URL)
        db = client_conn.get_database()
        chat_id = UUID(chat_id_str)

        # 1. Process PDF to get chunks and stats
        doc_id_str = str(uuid4())
        chunks, stats = pdf_processor.process_pdf(job_id, temp_path, doc_id_str, filename)
        
        if not chunks:
            raise Exception("No content extracted from PDF")

        upload_job.stage = ProcessingStage.ADDING_TO_VECTOR_STORE
        upload_job.progress = 0
        
        # 2. Add chunks to vector store
        collection = vector_store.get_or_create_collection(chat_id_str)
        added_count = vector_store.add_chunks(collection, chunks)
        
        upload_job.stage = ProcessingStage.SAVING_METADATA
        upload_job.progress = 0
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
        upload_job.status = ProcessingStatus.FINISHED
        upload_job.progress = 100
        upload_job.finished_at = now
        upload_job.chunks_added = added_count
        print(f"✅ PDF {filename} processed successfully for job {job_id}")

    except Exception as e:
        error_msg = str(e)
        print(f"❌ Processing error for job {job_id}: {error_msg}")
        traceback.print_exc()
        upload_job.status = ProcessingStatus.FAILED
        upload_job.error = error_msg
        upload_job.finished_at = get_consistent_timestamp()
    
    finally:
        if client_conn and client_conn.client:
            client_conn.client.close()
        # 6. Clean up temporary file
        try:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        except Exception as e:
            print(f"⚠️  Cleanup error for job {job_id}: {e}")

import os
from uuid import UUID, uuid4
import traceback
from datetime import datetime

from sqlalchemy.orm import Session
from langchain_core.documents import Document as LangChainDocument

from app.core.services import pdf_processor, vector_store
from app.core.global_stores import upload_jobs
from app.db.database import SessionLocal
from app.modules.askai.db.models import Document as SQLDocument, Chat as SQLChat, DocumentChunk
from app.modules.askai.models.document import ProcessingStage, ProcessingStatus, UploadJob
from app.utils import get_file_hash
from app.config import settings

def process_uploaded_pdf(temp_path: str, chat_id_str: str, filename: str, job_id: str):
    """Background task to process a PDF file using a new DB session."""
    upload_job = upload_jobs.get(job_id)
    if not isinstance(upload_job, UploadJob):
        return

    upload_job.status = ProcessingStatus.PROCESSING
    upload_job.stage = ProcessingStage.EXTRACTING_CONTENT
    upload_job.progress = 0

    db: Session = SessionLocal()
    try:
        chat_id = UUID(chat_id_str)
        chat = db.get(SQLChat, chat_id)
        if not chat:
            raise Exception(f"Chat {chat_id} not found in database.")

        # 1. Process PDF to get LangChain Documents and stats
        doc_id = uuid4()
        chunks, stats = pdf_processor.process_pdf(job_id, temp_path, str(doc_id), filename)
        
        if not chunks:
            raise Exception("No content extracted from PDF")

        upload_job.stage = ProcessingStage.ADDING_TO_VECTOR_STORE
        upload_job.progress = 0
        
        # 2. Add chunks to vector store
        collection = vector_store.get_or_create_collection(chat_id_str)
        chunks_for_store = [{"content": doc.page_content, "metadata": doc.metadata} for doc in chunks]
        added_count = vector_store.add_chunks(collection, chunks_for_store)
        
        upload_job.stage = ProcessingStage.SAVING_METADATA
        upload_job.progress = 0
        
        # 3. Save document and chunks to PostgreSQL
        now = datetime.now()
        new_document = SQLDocument(
            id=doc_id,
            filename=filename,
            file_hash=get_file_hash(temp_path),
            file_size=os.path.getsize(temp_path),
            uploaded_at=now,
            processing_stats=stats,
            chunks=[
                DocumentChunk(
                    content=doc.page_content,
                    chunk_metadata=doc.metadata,
                    embedding=[]  # Embedding is stored in Weaviate, not PG for now
                ) for doc in chunks
            ]
        )
        chat.documents.append(new_document)
        chat.updated_at = now
        db.commit()
        
        # 4. Update job status to 'done'
        upload_job.status = ProcessingStatus.FINISHED
        upload_job.progress = 100
        upload_job.finished_at = now.isoformat()
        upload_job.chunks_added = added_count
        print(f"✅ PDF {filename} processed successfully for job {job_id}")

    except Exception as e:
        error_msg = str(e)
        print(f"❌ Processing error for job {job_id}: {error_msg}")
        traceback.print_exc()
        upload_job.status = ProcessingStatus.FAILED
        upload_job.error = error_msg
        upload_job.finished_at = datetime.now().isoformat()
    
    finally:
        db.close()
        # 6. Clean up temporary file
        try:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        except Exception as e:
            print(f"⚠️  Cleanup error for job {job_id}: {e}")

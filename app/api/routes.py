"""
Defines all the API routes (endpoints) for the application.
This is the V in MVC, the layer that communicates with the outside world.
It calls the service layer for business logic and returns data conforming to schemas.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import traceback

from ..db.base import get_db
from ..models import schemas
from ..services import chat_service, document_service

router = APIRouter()

@router.get("/health", summary="Health Check")
def health_check():
    health_status = chat_service.get_health_status()
    return health_status

@router.get("/chats", response_model=List[schemas.ChatResponse])
def get_chats(db: Session = Depends(get_db)):
    return chat_service.get_all_chats(db)

@router.post("/chats", response_model=schemas.ChatResponse, status_code=201)
def create_chat(db: Session = Depends(get_db)):
    return chat_service.create_new_chat(db)

@router.get("/chats/{chat_id}", response_model=List[schemas.MessageResponse])
def get_chat(chat_id: str, db: Session = Depends(get_db)):
    return chat_service.get_chat_messages(db, chat_id)

@router.delete("/chats/{chat_id}")
def delete_chat(chat_id: str, db: Session = Depends(get_db)):
    chat_service.delete_chat(db, chat_id)
    return {"message": "Chat deleted successfully"}

@router.put("/chats/{chat_id}/rename")
def rename_chat(chat_id: str, request_body: schemas.RenameChatRequest, db: Session = Depends(get_db)):
    chat_service.rename_chat(db, chat_id, request_body.title)
    return {"message": "Chat renamed successfully"}

@router.post("/chats/{chat_id}/messages", response_model=schemas.BotReply)
def send_message(chat_id: str, request_body: schemas.SendMessageRequest, db: Session = Depends(get_db)):
    try:
        return chat_service.handle_send_message(db, chat_id, request_body.message)
    except Exception as e:
        print(f"❌ Message error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chats/{chat_id}/upload-pdf", response_model=schemas.UploadAcceptedResponse, status_code=202)
def upload_pdf(chat_id: str, pdf: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        response = document_service.handle_pdf_upload(db, chat_id, pdf)
        return response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/upload-status/{job_id}", response_model=schemas.UploadStatusResponse)
def get_upload_status(job_id: str):
    status = document_service.get_upload_job_status(job_id)
    if not status:
        raise HTTPException(status_code=404, detail="Job not found")
    return status

@router.get("/chats/{chat_id}/pdfs", response_model=schemas.ChatPdfsResponse)
def get_chat_pdfs(chat_id: str, db: Session = Depends(get_db)):
    return chat_service.get_chat_pdfs_info(db, chat_id)

@router.delete("/chats/{chat_id}/pdfs/{pdf_name}")
def delete_chat_pdf(chat_id: str, pdf_name: str, db: Session = Depends(get_db)):
    document_service.delete_pdf_from_chat(db, chat_id, pdf_name)
    return {"message": "PDF removed successfully", "chat_id": chat_id, "pdf_name": pdf_name}

@router.get("/pdfs") # Not in the old UI, but present in the server code
def get_all_pdfs(db: Session = Depends(get_db)):
    return chat_service.get_all_pdfs_across_chats(db)



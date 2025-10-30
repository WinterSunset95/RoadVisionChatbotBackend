from uuid import UUID
from typing import List, Optional
from fastapi import BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime

from app.core.services import vector_store
from app.modules.askai.models.chat import ChatMetadata, Message, CreateNewChatRequest, DocumentMetadata
from app.modules.askai.db.models import Chat as SQLChat
from app.modules.askai.services.drive_service import download_files_from_drive

def get_all_chats(db: Session) -> List[ChatMetadata]:
    """Get all chats from PostgreSQL."""
    chats = db.query(SQLChat).order_by(desc(SQLChat.updated_at)).all()
    response_chats = []
    for chat in chats:
        pdf_list = [
            DocumentMetadata(
                name=doc.filename,
                chunks=len(doc.chunks),
                status=doc.status
            ) for doc in chat.documents
        ]
        response_chats.append(
            ChatMetadata(
                id=chat.id,
                title=chat.title,
                created_at=chat.created_at.isoformat(),
                updated_at=chat.updated_at.isoformat(),
                message_count=len(chat.messages),
                pdf_count=len(chat.documents),
                pdf_list=pdf_list,
            )
        )
    return response_chats

def create_new_chat(db: Session, payload: Optional[CreateNewChatRequest], background_tasks: BackgroundTasks) -> ChatMetadata:
    """Create a new chat session in PostgreSQL."""
    now = datetime.now()
    chat_count = db.query(SQLChat).count()
    new_chat = SQLChat(
        title=f"New Chat {chat_count + 1}",
        created_at=now,
        updated_at=now,
    )
    db.add(new_chat)
    db.commit()
    db.refresh(new_chat)

    if payload and payload.driveUrl:
        background_tasks.add_task(download_files_from_drive, payload.driveUrl, str(new_chat.id))

    return ChatMetadata(
        id=new_chat.id,
        title=new_chat.title,
        created_at=new_chat.created_at.isoformat(),
        updated_at=new_chat.updated_at.isoformat(),
        message_count=0,
        pdf_count=0,
        pdf_list=[],
    )

def get_chat_messages(db: Session, chat_id: UUID) -> List[Message]:
    """Get all messages for a specific chat from PostgreSQL."""
    chat = db.get(SQLChat, chat_id)
    if not chat:
        return []
    
    return [Message.model_validate(msg) for msg in chat.messages]

def delete_chat_by_id(db: Session, chat_id: UUID) -> bool:
    """Delete a chat session and its associated data from PostgreSQL."""
    chat = db.get(SQLChat, chat_id)
    if not chat:
        return False
    
    db.delete(chat)
    db.commit()
    vector_store.delete_collection(str(chat_id))
    return True

def rename_chat_by_id(db: Session, chat_id: UUID, new_title: str) -> bool:
    """Rename a chat session in PostgreSQL."""
    chat = db.get(SQLChat, chat_id)
    if not chat:
        return False
    
    chat.title = new_title
    chat.updated_at = datetime.now()
    db.commit()
    return True

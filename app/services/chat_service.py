import uuid
from typing import List
from sqlalchemy.orm import Session

from app.db import crud
from app.core.services import vector_store
from app.models.chat import ChatMetadata, Message

def get_all_chats(db: Session) -> List[ChatMetadata]:
    """Get all chats, converting them to Pydantic models."""
    db_chats = crud.get_chats(db)
    response_chats = []
    for chat in db_chats:
        docs = crud.get_chat_documents(db, chat.id)
        messages = crud.get_chat_messages(db, chat.id)
        
        pdf_list = [{
            "name": doc.filename,
            "upload_time": doc.uploaded_at.isoformat(),
            "chunks_added": doc.chunks_count,
            "status": doc.status
        } for doc in docs]
        
        response_chats.append(
            ChatMetadata(
                id=chat.id,
                title=chat.title,
                created_at=chat.created_at.isoformat(),
                updated_at=chat.updated_at.isoformat() if chat.updated_at else chat.created_at.isoformat(),
                message_count=len(messages),
                has_pdf=len(docs) > 0,
                pdf_count=len(docs),
                pdf_list=pdf_list
            )
        )
    return response_chats

def create_new_chat(db: Session) -> ChatMetadata:
    """Create a new chat session."""
    # To determine the title, we need the count of existing chats.
    chat_count = db.query(crud.models.Chat).count()
    new_chat = crud.create_chat(db, title=f"New Chat {chat_count + 1}")
    
    # Convert to Pydantic model for response, ensuring all fields are present
    return ChatMetadata(
        id=new_chat.id,
        title=new_chat.title,
        created_at=new_chat.created_at.isoformat(),
        updated_at=new_chat.updated_at.isoformat() if new_chat.updated_at else new_chat.created_at.isoformat(),
        message_count=0,
        has_pdf=False,
        pdf_count=0,
        pdf_list=[]
    )

def get_chat_messages(db: Session, chat_id: uuid.UUID) -> List[Message]:
    """Get all messages for a specific chat, converted to Pydantic models."""
    db_messages = crud.get_chat_messages(db, chat_id)
    return [Message.model_validate(msg) for msg in db_messages]

def delete_chat_by_id(db: Session, chat_id: uuid.UUID) -> bool:
    """Delete a chat session and its associated data."""
    chat_to_delete = crud.get_chat(db, chat_id)
    if not chat_to_delete:
        return False

    crud.delete_chat(db, chat_to_delete)
    vector_store.delete_collection(str(chat_id))
    return True

def rename_chat_by_id(db: Session, chat_id: uuid.UUID, new_title: str) -> bool:
    """Rename a chat session."""
    chat_to_rename = crud.get_chat(db, chat_id)
    if not chat_to_rename:
        return False
    
    crud.rename_chat(db, chat_to_rename, new_title)
    return True

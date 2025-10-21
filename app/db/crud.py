import uuid
from typing import List, Dict, Any, Optional

from sqlalchemy.orm import Session, joinedload
from app.db import models
from app.utils import get_consistent_timestamp

# --- Chat CRUD ---

def get_chat(db: Session, chat_id: uuid.UUID) -> Optional[models.Chat]:
    """Get a single chat by its ID, with documents preloaded."""
    return db.query(models.Chat).options(joinedload(models.Chat.documents)).filter(models.Chat.id == chat_id).first()

def get_chats(db: Session) -> List[models.Chat]:
    """Get all chats, ordered by last updated."""
    return db.query(models.Chat).order_by(models.Chat.updated_at.desc()).all()

def create_chat(db: Session, title: str) -> models.Chat:
    """Create a new chat session."""
    new_chat = models.Chat(title=title, updated_at=get_consistent_timestamp())
    db.add(new_chat)
    db.commit()
    db.refresh(new_chat)
    return new_chat

def delete_chat(db: Session, chat: models.Chat):
    """Delete a chat session."""
    db.delete(chat)
    db.commit()

def rename_chat(db: Session, chat: models.Chat, new_title: str) -> models.Chat:
    """Rename a chat session."""
    chat.title = new_title
    chat.updated_at = get_consistent_timestamp()
    db.commit()
    db.refresh(chat)
    return chat

# --- Message CRUD ---

def get_chat_messages(db: Session, chat_id: uuid.UUID) -> List[models.Message]:
    """Get all messages for a specific chat."""
    return db.query(models.Message).filter(models.Message.chat_id == chat_id).order_by(models.Message.timestamp.asc()).all()

def add_message(db: Session, chat_id: uuid.UUID, sender: str, text: str) -> models.Message:
    """Add a new message to a chat and update the chat's timestamp."""
    message = models.Message(chat_id=chat_id, sender=sender, text=text)
    db.add(message)
    
    # Also update the parent chat's updated_at timestamp
    chat = db.query(models.Chat).filter(models.Chat.id == chat_id).first()
    if chat:
        chat.updated_at = get_consistent_timestamp()

    db.commit()
    db.refresh(message)
    return message

# --- Document CRUD ---

def get_document_by_hash(db: Session, file_hash: str) -> Optional[models.Document]:
    """Get a document by its file hash."""
    return db.query(models.Document).filter(models.Document.file_hash == file_hash).first()

def create_document(db: Session, chat_id: uuid.UUID, doc_data: Dict[str, Any]) -> models.Document:
    """Create a new document record."""
    document = models.Document(chat_id=chat_id, **doc_data)
    db.add(document)
    
    # Update parent chat's timestamp
    chat = db.query(models.Chat).filter(models.Chat.id == chat_id).first()
    if chat:
        chat.updated_at = get_consistent_timestamp()
    
    db.commit()
    db.refresh(document)
    return document

def get_chat_documents(db: Session, chat_id: uuid.UUID) -> List[models.Document]:
    """Get all documents for a specific chat."""
    return db.query(models.Document).filter(models.Document.chat_id == chat_id).all()

def delete_document(db: Session, doc_to_delete: models.Document):
    """Delete a document record."""
    chat = doc_to_delete.chat
    db.delete(doc_to_delete)
    
    # Update parent chat's timestamp
    if chat:
        chat.updated_at = get_consistent_timestamp()
        
    db.commit()

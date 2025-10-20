"""
CRUD (Create, Read, Update, Delete) operations for the database.

This module contains functions that directly interact with the database using
SQLAlchemy sessions and models. It abstracts the raw database queries from
the business logic in the service layer.
"""
import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime

from . import models
from ..models import schemas
from ..utils import helpers

# --- Chat CRUD Operations ---

def get_chat(db: Session, chat_id: str) -> Optional[models.Chat]:
    """Retrieves a single chat from the database by its ID."""
    return db.query(models.Chat).filter(models.Chat.id == chat_id).first()

def get_all_chats(db: Session) -> List[models.Chat]:
    """Retrieves all chats from the database, ordered by the most recently updated."""
    return db.query(models.Chat).order_by(desc(models.Chat.updated_at)).all()

def create_chat(db: Session, title: str) -> models.Chat:
    """Creates a new chat record in the database."""
    timestamp = datetime.now()
    db_chat = models.Chat(
        id=str(uuid.uuid4()),
        title=title,
        created_at=timestamp,
        updated_at=timestamp,
        pdf_list=[]
    )
    db.add(db_chat)
    db.commit()
    db.refresh(db_chat)
    return db_chat

def update_chat_metadata(db: Session, chat: models.Chat, **kwargs):
    """Updates specified attributes of a chat and commits the changes."""
    for key, value in kwargs.items():
        setattr(chat, key, value)
    chat.updated_at = datetime.now()
    db.commit()
    db.refresh(chat)
    return chat

def delete_chat(db: Session, chat_id: str):
    """Deletes a chat and its associated messages from the database."""
    db_chat = get_chat(db, chat_id)
    if db_chat:
        db.delete(db_chat)
        db.commit()

# --- Message CRUD Operations ---

def create_message(db: Session, chat_id: str, role: str, text: str, sources: Optional[List[dict]] = None) -> models.Message:
    """Creates a new message record and associates it with a chat."""
    db_message = models.Message(
        id=str(uuid.uuid4()),
        chat_id=chat_id,
        role=role,
        parts=[text],
        timestamp=datetime.now(),
        sources=sources or []
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message

def get_chat_messages(db: Session, chat_id: str) -> List[models.Message]:
    """Retrieves all messages for a specific chat, ordered by timestamp."""
    return db.query(models.Message).filter(models.Message.chat_id == chat_id).order_by(models.Message.timestamp).all()

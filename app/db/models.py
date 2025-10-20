"""
Defines the SQLAlchemy ORM models, representing the database tables.
"""
from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.orm import relationship
from .base import Base

class Chat(Base):
    __tablename__ = "chats"
    id = Column(String, primary_key=True, index=True)
    title = Column(String, index=True)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    pdf_list = Column(JSON, nullable=False, default=[])
    messages = relationship("Message", back_populates="chat", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"
    id = Column(String, primary_key=True, index=True)
    chat_id = Column(String, index=True)
    role = Column(String)  # 'user' or 'model'
    parts = Column(JSON)
    timestamp = Column(DateTime)
    sources = Column(JSON, nullable=True, default=[]) # Storing sources with the bot's message
    chat = relationship("Chat", back_populates="messages")



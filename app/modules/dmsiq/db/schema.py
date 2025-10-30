import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.database import Base

class DmsFolder(Base):
    __tablename__ = 'dms_folders'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey('dms_folders.id'), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    files = relationship("DmsFile", back_populates="folder")
    subfolders = relationship("DmsFolder") # Self-referencing relationship

class DmsFile(Base):
    __tablename__ = 'dms_files'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    folder_id = Column(UUID(as_uuid=True), ForeignKey('dms_folders.id'), nullable=False)
    file_path = Column(String, nullable=False, unique=True)
    file_type = Column(String)
    file_size = Column(Integer)
    metadata = Column(JSON)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    folder = relationship("DmsFolder", back_populates="files")

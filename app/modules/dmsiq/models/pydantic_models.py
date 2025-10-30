from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from uuid import UUID
from datetime import datetime

class DmsFileBase(BaseModel):
    name: str
    file_type: Optional[str] = None
    file_size: Optional[int] = None

class DmsFileCreate(DmsFileBase):
    folder_id: UUID

class DmsFile(DmsFileBase):
    id: UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class DmsFolderBase(BaseModel):
    name: str
    parent_id: Optional[UUID] = None

class DmsFolderCreate(DmsFolderBase):
    pass

class DmsFolder(DmsFolderBase):
    id: UUID
    files: List[DmsFile] = []
    subfolders: List['DmsFolder'] = []
    model_config = ConfigDict(from_attributes=True)

DmsFolder.model_rebuild()

from pydantic import BaseModel, ConfigDict
from typing import Optional
from uuid import UUID
from datetime import datetime

class TenderBase(BaseModel):
    tender_title: str
    description: Optional[str] = None
    status: str = 'New'

class TenderCreate(TenderBase):
    pass

class Tender(TenderBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class TenderAnalysisBase(BaseModel):
    tender_id: UUID
    executive_summary: Optional[str] = None

class TenderAnalysisCreate(TenderAnalysisBase):
    pass

class TenderAnalysis(TenderAnalysisBase):
    id: UUID
    analyzed_at: datetime
    model_config = ConfigDict(from_attributes=True)

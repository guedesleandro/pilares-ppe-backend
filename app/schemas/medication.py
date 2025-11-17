from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class MedicationBase(BaseModel):
    name: str


class MedicationCreate(MedicationBase):
    name: str


class MedicationUpdate(BaseModel):
    name: Optional[str] = None


class MedicationResponse(BaseModel):
    id: UUID
    name: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)



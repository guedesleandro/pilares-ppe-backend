from pydantic import BaseModel, ConfigDict
from datetime import datetime
from uuid import UUID
from typing import Optional

from app.schemas.medication import MedicationResponse
from app.schemas.body_composition import BodyCompositionCreate, BodyCompositionResponse
from app.schemas.activator import ActivatorResponse


class SessionCreate(BaseModel):
    cycle_id: UUID
    session_date: datetime
    notes: Optional[str] = None
    medication_id: UUID
    activator_id: Optional[UUID] = None
    dosage_mg: Optional[float] = None
    body_composition: BodyCompositionCreate


class SessionUpdate(BaseModel):
    session_date: Optional[datetime] = None
    notes: Optional[str] = None
    medication_id: Optional[UUID] = None
    activator_id: Optional[UUID] = None
    dosage_mg: Optional[float] = None
    body_composition: Optional[BodyCompositionCreate] = None


class SessionResponse(BaseModel):
    id: UUID
    cycle_id: UUID
    medication_id: UUID
    activator_id: Optional[UUID] = None
    dosage_mg: Optional[float] = None
    session_date: datetime
    notes: Optional[str]
    created_at: datetime
    medication: Optional[MedicationResponse] = None
    activator: Optional[ActivatorResponse] = None
    body_composition: Optional[BodyCompositionResponse] = None

    model_config = ConfigDict(from_attributes=True)


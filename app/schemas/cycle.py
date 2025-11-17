from pydantic import BaseModel, ConfigDict, field_validator
from datetime import datetime
from uuid import UUID
from typing import Optional, List
from app.models.cycle import PeriodicityEnum, CycleTypeEnum


class CycleCreate(BaseModel):
    patient_id: UUID
    max_sessions: int
    periodicity: PeriodicityEnum
    type: CycleTypeEnum = CycleTypeEnum.normal

    @field_validator('max_sessions')
    @classmethod
    def validate_max_sessions(cls, v):
        if v < 0:
            raise ValueError('max_sessions deve ser maior que 1')
        return v


class CycleUpdate(BaseModel):
    max_sessions: Optional[int] = None
    periodicity: Optional[PeriodicityEnum] = None
    type: Optional[CycleTypeEnum] = None

    @field_validator('max_sessions')
    @classmethod
    def validate_max_sessions(cls, v):
        if v is not None and v < 0:
            raise ValueError('max_sessions deve ser maior que 1')
        return v


class CycleResponse(BaseModel):
    id: UUID
    patient_id: UUID
    max_sessions: int
    periodicity: PeriodicityEnum
    type: CycleTypeEnum
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


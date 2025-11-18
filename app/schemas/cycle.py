from pydantic import BaseModel, ConfigDict, Field, field_validator
from datetime import datetime
from uuid import UUID
from typing import Optional, List

from app.models.cycle import PeriodicityEnum, CycleTypeEnum
from app.schemas.session import SessionResponse


class CycleBase(BaseModel):
    max_sessions: int
    periodicity: PeriodicityEnum
    type: CycleTypeEnum = CycleTypeEnum.normal
    cycle_date: datetime

    @field_validator("max_sessions")
    @classmethod
    def validate_max_sessions(cls, value: int) -> int:
        if value < 1:
            raise ValueError("max_sessions deve ser maior que 1")
        return value


class CycleCreate(CycleBase):
    patient_id: UUID


class CycleForPatientCreate(CycleBase):
    """
    Comentário em pt-BR: payload para criar ciclo usando rota aninhada do paciente
    """


class CycleUpdate(BaseModel):
    max_sessions: Optional[int] = None
    periodicity: Optional[PeriodicityEnum] = None
    type: Optional[CycleTypeEnum] = None
    cycle_date: Optional[datetime] = None

    @field_validator("max_sessions")
    @classmethod
    def validate_max_sessions(cls, value: Optional[int]) -> Optional[int]:
        if value is not None and value < 1:
            raise ValueError("max_sessions deve ser maior que 1")
        return value


class CycleResponse(BaseModel):
    id: UUID
    patient_id: UUID
    max_sessions: int
    periodicity: PeriodicityEnum
    type: CycleTypeEnum
    cycle_date: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CycleWithSessionsResponse(CycleResponse):
    sessions: List[SessionResponse] = Field(default_factory=list)


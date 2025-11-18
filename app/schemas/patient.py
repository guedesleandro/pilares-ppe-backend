from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.patient import GenderEnum, PatientStatusEnum, TreatmentLocationEnum
from app.schemas.medication import MedicationResponse


class PatientCreate(BaseModel):
    name: str
    gender: GenderEnum
    birth_date: date
    process_number: Optional[str] = None
    treatment_location: TreatmentLocationEnum = TreatmentLocationEnum.clinic
    status: PatientStatusEnum = PatientStatusEnum.active
    preferred_medication_id: Optional[UUID] = None


class PatientUpdate(BaseModel):
    name: Optional[str] = None
    gender: Optional[GenderEnum] = None
    birth_date: Optional[date] = None
    process_number: Optional[str] = None
    treatment_location: Optional[TreatmentLocationEnum] = None
    status: Optional[PatientStatusEnum] = None
    preferred_medication_id: Optional[UUID] = None


class PatientResponse(BaseModel):
    id: UUID
    name: str
    gender: GenderEnum
    birth_date: date
    process_number: Optional[str]
    treatment_location: TreatmentLocationEnum
    status: PatientStatusEnum
    preferred_medication: Optional[MedicationResponse] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class PatientListItemResponse(BaseModel):
    """
    Comentário em pt-BR: schema resumido para listagem de pacientes com metadados agregados
    """
    id: UUID
    name: str
    process_number: Optional[str]
    gender: GenderEnum
    age: int
    current_cycle_number: int
    last_session_date: Optional[datetime]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PatientsListResponse(BaseModel):
    """
    Comentário em pt-BR: envelope com resultados paginados por página clássica
    """
    items: List[PatientListItemResponse]
    page: int
    page_size: int
    total: int
    has_next: bool


class BodyCompositionSummary(BaseModel):
    """
    Comentário em pt-BR: resumo da composição corporal para a Ficha de Cliente
    """

    registered_at: datetime
    weight_kg: Decimal
    fat_percentage: Decimal
    fat_kg: Decimal
    muscle_mass_kg: Decimal
    h2o_percentage: Decimal
    metabolic_age: int
    visceral_fat: int


class PatientSummary(BaseModel):
    """
    Comentário em pt-BR: resumo consolidado do paciente para a Ficha de Cliente
    """

    id: UUID
    name: str
    process_number: Optional[str]
    birth_date: date
    gender: GenderEnum
    treatment_location: TreatmentLocationEnum
    status: PatientStatusEnum
    preferred_medication: Optional[MedicationResponse]
    created_at: datetime
    first_session_date: Optional[datetime]
    last_session_date: Optional[datetime]
    body_composition_initial: Optional[BodyCompositionSummary]
    body_composition_latest: Optional[BodyCompositionSummary]

    model_config = ConfigDict(from_attributes=True)

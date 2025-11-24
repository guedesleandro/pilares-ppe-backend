from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class BodyCompositionBase(BaseModel):
    weight_kg: Decimal
    fat_percentage: Decimal
    fat_kg: Decimal
    muscle_mass_percentage: Decimal
    h2o_percentage: Decimal
    metabolic_age: int
    visceral_fat: int


class BodyCompositionCreate(BodyCompositionBase):
    """
    Medidas obrigatórias para registrar a composição corporal.
    """


class BodyCompositionResponse(BodyCompositionBase):
    """
    Retorno da composição corporal vinculada à sessão e paciente.
    """

    id: UUID
    patient_id: UUID
    session_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


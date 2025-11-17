from datetime import datetime
from uuid import UUID
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class ActivatorCompositionItem(BaseModel):
    substance_id: UUID
    volume_ml: float


class ActivatorCreate(BaseModel):
    name: str
    compositions: List[ActivatorCompositionItem]


class ActivatorUpdate(BaseModel):
    name: Optional[str] = None
    compositions: Optional[List[ActivatorCompositionItem]] = None


class ActivatorCompositionResponse(BaseModel):
    substance_id: UUID
    volume_ml: float
    substance_name: str


class ActivatorResponse(BaseModel):
    id: UUID
    name: str
    created_at: datetime
    compositions: List[ActivatorCompositionResponse]

    model_config = ConfigDict(from_attributes=True)



from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class SubstanceCreate(BaseModel):
    name: str


class SubstanceUpdate(BaseModel):
    name: str | None = None


class SubstanceResponse(BaseModel):
    id: UUID
    name: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)



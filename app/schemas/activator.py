from datetime import datetime
from uuid import UUID
from typing import List, Optional, Any

from pydantic import BaseModel, ConfigDict, model_validator


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

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def build_substance_name(cls, data: Any) -> Any:
        """
        Comentário em pt-BR: constrói substance_name a partir do relacionamento substance.name
        quando o objeto é um modelo SQLAlchemy
        """
        # Se já é um dicionário, retorna como está
        if isinstance(data, dict):
            return data
        
        # Se é um objeto SQLAlchemy com relacionamento carregado
        if hasattr(data, "substance") and data.substance is not None:
            if hasattr(data.substance, "name"):
                return {
                    "substance_id": data.substance_id,
                    "volume_ml": data.volume_ml,
                    "substance_name": data.substance.name,
                }
        
        # Caso contrário, tenta usar from_attributes
        return data


class ActivatorResponse(BaseModel):
    id: UUID
    name: str
    created_at: datetime
    compositions: List[ActivatorCompositionResponse]

    model_config = ConfigDict(from_attributes=True)



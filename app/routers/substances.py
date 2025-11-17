from uuid import UUID
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.substance import Substance
from app.schemas.substance import (
    SubstanceCreate,
    SubstanceUpdate,
    SubstanceResponse,
)
from app.auth import get_current_user
from app.schemas.user import UserResponse


router = APIRouter(prefix="/substances", tags=["substances"])


@router.post("", response_model=SubstanceResponse, status_code=status.HTTP_201_CREATED)
async def create_substance(
    substance_data: SubstanceCreate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Criar nova substância
    """
    new_substance = Substance(**substance_data.model_dump())
    db.add(new_substance)
    db.commit()
    db.refresh(new_substance)
    return SubstanceResponse.model_validate(new_substance)


@router.get("", response_model=List[SubstanceResponse])
async def list_substances(
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Listar todas as substâncias
    """
    substances = db.query(Substance).all()
    return [SubstanceResponse.model_validate(substance) for substance in substances]


@router.get("/{substance_id}", response_model=SubstanceResponse)
async def get_substance(
    substance_id: UUID,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Buscar substância por ID
    """
    substance = db.query(Substance).filter(Substance.id == substance_id).first()
    if not substance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Substance not found",
        )
    return SubstanceResponse.model_validate(substance)


@router.put("/{substance_id}", response_model=SubstanceResponse)
async def update_substance(
    substance_id: UUID,
    substance_data: SubstanceUpdate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Atualizar substância
    """
    substance = db.query(Substance).filter(Substance.id == substance_id).first()
    if not substance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Substance not found",
        )

    update_data = substance_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(substance, field, value)

    db.commit()
    db.refresh(substance)
    return SubstanceResponse.model_validate(substance)


@router.delete("/{substance_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_substance(
    substance_id: UUID,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Deletar substância
    """
    substance = db.query(Substance).filter(Substance.id == substance_id).first()
    if not substance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Substance not found",
        )

    db.delete(substance)
    db.commit()
    return None



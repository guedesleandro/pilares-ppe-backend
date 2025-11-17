from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models.medication import Medication
from app.schemas.medication import (
    MedicationCreate,
    MedicationUpdate,
    MedicationResponse,
)
from app.schemas.user import UserResponse


router = APIRouter(prefix="/medications", tags=["medications"])


@router.post("", response_model=MedicationResponse, status_code=status.HTTP_201_CREATED)
async def create_medication(
    medication_data: MedicationCreate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Criar nova medicação
    """
    new_medication = Medication(**medication_data.model_dump())
    db.add(new_medication)
    db.commit()
    db.refresh(new_medication)
    return MedicationResponse.model_validate(new_medication)


@router.get("", response_model=List[MedicationResponse])
async def list_medications(
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Listar medicações cadastradas
    """
    medications = db.query(Medication).order_by(Medication.name).all()
    return [MedicationResponse.model_validate(medication) for medication in medications]


@router.get("/{medication_id}", response_model=MedicationResponse)
async def get_medication(
    medication_id: UUID,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Buscar medicação por ID
    """
    medication = db.query(Medication).filter(Medication.id == medication_id).first()
    if not medication:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medication not found",
        )

    return MedicationResponse.model_validate(medication)


@router.put("/{medication_id}", response_model=MedicationResponse)
async def update_medication(
    medication_id: UUID,
    medication_data: MedicationUpdate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Atualizar medicação
    """
    medication = db.query(Medication).filter(Medication.id == medication_id).first()
    if not medication:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medication not found",
        )

    update_data = medication_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(medication, field, value)

    db.commit()
    db.refresh(medication)
    return MedicationResponse.model_validate(medication)


@router.delete("/{medication_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_medication(
    medication_id: UUID,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Deletar medicação
    """
    medication = db.query(Medication).filter(Medication.id == medication_id).first()
    if not medication:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medication not found",
        )

    try:
        db.delete(medication)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete medication linked to sessions",
        )

    return None



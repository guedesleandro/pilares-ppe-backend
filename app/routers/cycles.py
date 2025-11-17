from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.cycle import Cycle
from app.models.patient import Patient
from app.schemas.cycle import CycleCreate, CycleUpdate, CycleResponse
from app.auth import get_current_user
from app.schemas.user import UserResponse

router = APIRouter(prefix="/cycles", tags=["cycles"])


@router.post("", response_model=CycleResponse, status_code=status.HTTP_201_CREATED)
async def create_cycle(
    cycle_data: CycleCreate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Criar novo ciclo para um paciente
    """
    # Verificar se o paciente existe
    patient = db.query(Patient).filter(Patient.id == cycle_data.patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    new_cycle = Cycle(**cycle_data.model_dump())
    db.add(new_cycle)
    db.commit()
    db.refresh(new_cycle)
    return CycleResponse.model_validate(new_cycle)


@router.get("", response_model=List[CycleResponse])
async def list_cycles(
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Listar todos os ciclos
    """
    cycles = db.query(Cycle).all()
    return [CycleResponse.model_validate(cycle) for cycle in cycles]


@router.get("/{cycle_id}", response_model=CycleResponse)
async def get_cycle(
    cycle_id: UUID,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Buscar ciclo por ID
    """
    cycle = db.query(Cycle).filter(Cycle.id == cycle_id).first()
    if not cycle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cycle not found"
        )
    return CycleResponse.model_validate(cycle)


@router.put("/{cycle_id}", response_model=CycleResponse)
async def update_cycle(
    cycle_id: UUID,
    cycle_data: CycleUpdate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Atualizar ciclo
    """
    cycle = db.query(Cycle).filter(Cycle.id == cycle_id).first()
    if not cycle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cycle not found"
        )
    
    # Atualiza apenas campos fornecidos
    update_data = cycle_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(cycle, field, value)
    
    db.commit()
    db.refresh(cycle)
    return CycleResponse.model_validate(cycle)


@router.delete("/{cycle_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cycle(
    cycle_id: UUID,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Deletar ciclo
    """
    cycle = db.query(Cycle).filter(Cycle.id == cycle_id).first()
    if not cycle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cycle not found"
        )
    
    db.delete(cycle)
    db.commit()
    return None


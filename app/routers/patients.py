from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.patient import Patient
from app.models.medication import Medication
from app.schemas.patient import PatientCreate, PatientUpdate, PatientResponse
from app.schemas.cycle import CycleResponse
from app.models.cycle import Cycle
from app.auth import get_current_user
from app.schemas.user import UserResponse

router = APIRouter(prefix="/patients", tags=["patients"])


def _validate_medication(
    db: Session,
    medication_id: Optional[UUID],
) -> None:
    if medication_id is None:
        return

    exists = db.query(Medication).filter(Medication.id == medication_id).first()
    if not exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medication not found",
        )


@router.post("", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
async def create_patient(
    patient_data: PatientCreate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Criar novo paciente
    """
    _validate_medication(db, patient_data.preferred_medication_id)

    new_patient = Patient(**patient_data.model_dump())
    db.add(new_patient)
    db.commit()
    db.refresh(new_patient)
    return PatientResponse.model_validate(new_patient)


@router.get("", response_model=List[PatientResponse])
async def list_patients(
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Listar todos os pacientes
    """
    patients = db.query(Patient).all()
    return [PatientResponse.model_validate(patient) for patient in patients]


@router.get("/search", response_model=List[PatientResponse])
async def search_patients(
    name: Optional[str] = Query(None, min_length=1, description="Parte do nome"),
    limit: int = Query(20, gt=0, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Buscar pacientes por parte do nome com paginação
    """
    query = db.query(Patient)
    if name:
        query = query.filter(Patient.name.ilike(f"%{name}%"))
    patients = (
        query
        .order_by(Patient.name)
        .limit(limit)
        .offset(offset)
        .all()
    )
    return [PatientResponse.model_validate(patient) for patient in patients]


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: UUID,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Buscar paciente por ID
    """
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    return PatientResponse.model_validate(patient)


@router.put("/{patient_id}", response_model=PatientResponse)
async def update_patient(
    patient_id: UUID,
    patient_data: PatientUpdate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Atualizar paciente
    """
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    # Atualiza apenas campos fornecidos
    update_data = patient_data.model_dump(exclude_unset=True)
    preferred_medication_id = update_data.get("preferred_medication_id")
    _validate_medication(db, preferred_medication_id)

    for field, value in update_data.items():
        setattr(patient, field, value)
    
    db.commit()
    db.refresh(patient)
    return PatientResponse.model_validate(patient)


@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_patient(
    patient_id: UUID,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Deletar paciente
    """
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    db.delete(patient)
    db.commit()
    return None


@router.get("/{patient_id}/cycles", response_model=List[CycleResponse])
async def list_patient_cycles(
    patient_id: UUID,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Listar todos os ciclos de um paciente específico
    """
    # Verificar se o paciente existe
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )

    cycles = db.query(Cycle).filter(Cycle.patient_id == patient_id).all()
    return [CycleResponse.model_validate(cycle) for cycle in cycles]


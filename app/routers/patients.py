from uuid import UUID
from typing import Optional, List
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.patient import Patient
from app.models.medication import Medication
from app.models.session import Session as SessionModel
from app.schemas.patient import (
    PatientCreate,
    PatientUpdate,
    PatientResponse,
    PatientListItemResponse,
    PatientsListResponse,
)
from app.schemas.cycle import CycleResponse
from app.models.cycle import Cycle
from app.auth import get_current_user
from app.schemas.user import UserResponse

router = APIRouter(prefix="/patients", tags=["patients"])


def _calculate_age(birth_date: date) -> int:
    """
    Comentário em pt-BR: calcula idade a partir da data de nascimento
    """
    today = date.today()
    years = today.year - birth_date.year
    if (today.month, today.day) < (birth_date.month, birth_date.day):
        years -= 1
    return years


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


@router.get("/listing", response_model=PatientsListResponse)
async def list_patients_with_metadata(
    search: Optional[str] = Query(None, min_length=1, description="Parte do nome"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, gt=0, le=100),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Comentário em pt-BR: lista pacientes com metadados agregados usando paginação tradicional
    """
    cycle_count_subquery = (
        db.query(
            Cycle.patient_id.label("patient_id"),
            func.count(Cycle.id).label("cycle_count"),
        )
        .group_by(Cycle.patient_id)
        .subquery()
    )

    last_session_subquery = (
        db.query(
            Cycle.patient_id.label("patient_id"),
            func.max(SessionModel.session_date).label("last_session_date"),
        )
        .join(SessionModel, SessionModel.cycle_id == Cycle.id)
        .group_by(Cycle.patient_id)
        .subquery()
    )

    base_filter = db.query(Patient)
    if search:
        base_filter = base_filter.filter(Patient.name.ilike(f"%{search}%"))
    total = base_filter.count()

    query = (
        db.query(
            Patient,
            func.coalesce(cycle_count_subquery.c.cycle_count, 0).label(
                "current_cycle_number"
            ),
            last_session_subquery.c.last_session_date.label("last_session_date"),
        )
        .outerjoin(
            cycle_count_subquery, cycle_count_subquery.c.patient_id == Patient.id
        )
        .outerjoin(
            last_session_subquery, last_session_subquery.c.patient_id == Patient.id
        )
    )

    if search:
        query = query.filter(Patient.name.ilike(f"%{search}%"))

    offset_value = (page - 1) * page_size

    results = (
        query.order_by(Patient.created_at.desc(), Patient.id.desc())
        .offset(offset_value)
        .limit(page_size)
        .all()
    )

    response_items: List[PatientListItemResponse] = []
    for patient, current_cycle_number, last_session_date in results:
        response_items.append(
            PatientListItemResponse(
                id=patient.id,
                name=patient.name,
                process_number=patient.process_number,
                gender=patient.gender,
                age=_calculate_age(patient.birth_date),
                current_cycle_number=current_cycle_number or 0,
                last_session_date=last_session_date,
                created_at=patient.created_at,
            )
        )

    has_next = page * page_size < total

    return PatientsListResponse(
        items=response_items,
        page=page,
        page_size=page_size,
        total=total,
        has_next=has_next,
    )


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


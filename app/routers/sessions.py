from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List

from app.database import get_db
from app.models.session import Session as SessionModel
from app.models.cycle import Cycle
from app.models.medication import Medication
from app.models.activator import Activator
from app.models.activator_composition import ActivatorComposition
from app.models.body_composition import BodyComposition
from app.schemas.session import SessionCreate, SessionUpdate, SessionResponse
from app.auth import get_current_user
from app.schemas.user import UserResponse

router = APIRouter(tags=["sessions"])


def _validate_medication(db: Session, medication_id: UUID) -> None:
    medication = db.query(Medication).filter(Medication.id == medication_id).first()
    if not medication:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medication not found",
        )


def _validate_activator(db: Session, activator_id: UUID) -> None:
    activator = db.query(Activator).filter(Activator.id == activator_id).first()
    if not activator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activator not found",
        )


@router.post("/cycles/{cycle_id}/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    cycle_id: UUID,
    session_data: SessionCreate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Criar nova sessão em um ciclo
    """
    # Verificar se o ciclo existe
    cycle = db.query(Cycle).filter(Cycle.id == cycle_id).first()
    if not cycle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cycle not found"
        )
    
    # Verificar se cycle_id do body corresponde ao da URL
    if session_data.cycle_id != cycle_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cycle ID in body does not match URL parameter"
        )
    
    _validate_medication(db, session_data.medication_id)
    
    if session_data.activator_id:
        _validate_activator(db, session_data.activator_id)

    # Verificar se já atingiu o máximo de sessões
    current_sessions_count = db.query(SessionModel).filter(SessionModel.cycle_id == cycle_id).count()
    if current_sessions_count >= cycle.max_sessions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cycle has reached maximum number of sessions ({cycle.max_sessions})"
        )
    
    session_payload = session_data.model_dump()
    body_composition_payload = session_payload.pop("body_composition")

    new_session = SessionModel(**session_payload)
    db.add(new_session)
    db.flush()

    body_composition = BodyComposition(
        patient_id=cycle.patient_id,
        session_id=new_session.id,
        **body_composition_payload,
    )
    db.add(body_composition)

    db.commit()
    
    # Recarregar a sessão com todos os relacionamentos necessários
    session_with_relations = (
        db.query(SessionModel)
        .options(
            joinedload(SessionModel.medication),
            joinedload(SessionModel.activator)
            .joinedload(Activator.compositions)
            .joinedload(ActivatorComposition.substance),
            joinedload(SessionModel.body_composition),
        )
        .filter(SessionModel.id == new_session.id)
        .first()
    )
    
    if not session_with_relations:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reload session after creation"
        )
    
    return SessionResponse.model_validate(session_with_relations)


@router.get("/cycles/{cycle_id}/sessions", response_model=List[SessionResponse])
async def list_cycle_sessions(
    cycle_id: UUID,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Listar todas as sessões de um ciclo específico
    """
    # Verificar se o ciclo existe
    cycle = db.query(Cycle).filter(Cycle.id == cycle_id).first()
    if not cycle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cycle not found"
        )
    
    sessions = (
        db.query(SessionModel)
        .options(
            joinedload(SessionModel.medication),
            joinedload(SessionModel.activator)
            .joinedload(Activator.compositions)
            .joinedload(ActivatorComposition.substance),
            joinedload(SessionModel.body_composition),
        )
        .filter(SessionModel.cycle_id == cycle_id)
        .all()
    )
    return [SessionResponse.model_validate(session) for session in sessions]


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Buscar sessão por ID
    """
    session = (
        db.query(SessionModel)
        .options(
            joinedload(SessionModel.medication),
            joinedload(SessionModel.activator)
            .joinedload(Activator.compositions)
            .joinedload(ActivatorComposition.substance),
            joinedload(SessionModel.body_composition),
        )
        .filter(SessionModel.id == session_id)
        .first()
    )
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    return SessionResponse.model_validate(session)


@router.put("/sessions/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: UUID,
    session_data: SessionUpdate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Atualizar sessão
    """
    session = (
        db.query(SessionModel)
        .options(joinedload(SessionModel.cycle))
        .filter(SessionModel.id == session_id)
        .first()
    )
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Atualiza apenas campos fornecidos
    update_data = session_data.model_dump(exclude_unset=True)
    body_composition_payload = update_data.pop("body_composition", None)
    if "medication_id" in update_data:
        medication_id = update_data["medication_id"]
        if medication_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Medication ID is required",
            )
        _validate_medication(db, medication_id)
    
    if "activator_id" in update_data and update_data["activator_id"] is not None:
        _validate_activator(db, update_data["activator_id"])

    for field, value in update_data.items():
        setattr(session, field, value)

    if body_composition_payload:
        if session.body_composition is None:
            session.body_composition = BodyComposition(
                patient_id=session.cycle.patient_id,
                session_id=session.id,
                **body_composition_payload,
            )
        else:
            for field, value in body_composition_payload.items():
                setattr(session.body_composition, field, value)
    
    db.commit()
    
    # Recarregar a sessão com todos os relacionamentos necessários
    session_with_relations = (
        db.query(SessionModel)
        .options(
            joinedload(SessionModel.medication),
            joinedload(SessionModel.activator)
            .joinedload(Activator.compositions)
            .joinedload(ActivatorComposition.substance),
            joinedload(SessionModel.body_composition),
        )
        .filter(SessionModel.id == session_id)
        .first()
    )
    
    if not session_with_relations:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reload session after update"
        )
    
    return SessionResponse.model_validate(session_with_relations)


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Deletar sessão
    """
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    db.delete(session)
    db.commit()
    return None


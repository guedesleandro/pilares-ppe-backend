from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Tuple
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc

from app.database import get_db
from app.models.patient import Patient
from app.models.session import Session as SessionModel
from app.models.body_composition import BodyComposition
from app.models.cycle import Cycle
from app.models.activator import Activator
from app.models.medication import Medication
from app.schemas.dashboard import DashboardStatsResponse, ActivatorUsageItem, MedicationPreferenceItem
from app.auth import get_current_user
from app.schemas.user import UserResponse

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Comentário em pt-BR: retorna estatísticas do dashboard com métricas e dados para gráficos
    """
    # Total de pacientes
    total_patients = db.query(func.count(Patient.id)).scalar() or 0

    # Sessões nos últimos 30 dias
    thirty_days_ago = datetime.now() - timedelta(days=30)
    sessions_last_30_days = (
        db.query(func.count(SessionModel.id))
        .filter(SessionModel.session_date >= thirty_days_ago)
        .scalar() or 0
    )

    # Total de kilos perdidos
    # Para cada paciente, buscar primeira e última body_composition
    total_weight_lost = Decimal("0.0")
    
    # Buscar todos os pacientes que têm pelo menos uma sessão com body_composition
    patients_with_sessions = (
        db.query(Patient.id)
        .join(Cycle, Cycle.patient_id == Patient.id)
        .join(SessionModel, SessionModel.cycle_id == Cycle.id)
        .join(BodyComposition, BodyComposition.session_id == SessionModel.id)
        .distinct()
        .all()
    )
    
    for (patient_id,) in patients_with_sessions:
        # Buscar primeira sessão com body_composition
        first_session = (
            db.query(SessionModel)
            .join(Cycle, Cycle.id == SessionModel.cycle_id)
            .join(BodyComposition, BodyComposition.session_id == SessionModel.id)
            .options(joinedload(SessionModel.body_composition))
            .filter(Cycle.patient_id == patient_id)
            .order_by(SessionModel.session_date)
            .first()
        )
        
        # Buscar última sessão com body_composition
        last_session = (
            db.query(SessionModel)
            .join(Cycle, Cycle.id == SessionModel.cycle_id)
            .join(BodyComposition, BodyComposition.session_id == SessionModel.id)
            .options(joinedload(SessionModel.body_composition))
            .filter(Cycle.patient_id == patient_id)
            .order_by(desc(SessionModel.session_date))
            .first()
        )
        
        if first_session and last_session and first_session.id != last_session.id:
            first_weight = first_session.body_composition.weight_kg
            last_weight = last_session.body_composition.weight_kg
            weight_diff = last_weight - first_weight
            total_weight_lost += weight_diff

    # Ativadores mais utilizados
    activators_usage_raw: List[Tuple[str, int]] = (
        db.query(Activator.name, func.count(SessionModel.id))
        .join(SessionModel, SessionModel.activator_id == Activator.id)
        .filter(SessionModel.activator_id.isnot(None))
        .group_by(Activator.id, Activator.name)
        .order_by(desc(func.count(SessionModel.id)))
        .all()
    )
    
    activators_usage = [
        ActivatorUsageItem(name=name, count=count)
        for name, count in activators_usage_raw
    ]

    # Medicação preferencial mais optada
    medications_preference_raw: List[Tuple[str, int]] = (
        db.query(Medication.name, func.count(Patient.id))
        .join(Patient, Patient.preferred_medication_id == Medication.id)
        .filter(Patient.preferred_medication_id.isnot(None))
        .group_by(Medication.id, Medication.name)
        .order_by(desc(func.count(Patient.id)))
        .all()
    )
    
    medications_preference = [
        MedicationPreferenceItem(name=name, count=count)
        for name, count in medications_preference_raw
    ]

    return DashboardStatsResponse(
        total_patients=total_patients,
        sessions_last_30_days=sessions_last_30_days,
        total_weight_lost_kg=float(total_weight_lost),
        activators_usage=activators_usage,
        medications_preference=medications_preference,
    )


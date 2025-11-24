from datetime import datetime, timedelta, date
from decimal import Decimal
from typing import List, Tuple, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc

from app.database import get_db
from app.models.patient import Patient, GenderEnum, TreatmentLocationEnum
from app.models.session import Session as SessionModel
from app.models.body_composition import BodyComposition
from app.models.cycle import Cycle
from app.models.activator import Activator
from app.models.medication import Medication
from app.schemas.dashboard import (
    DashboardStatsResponse, 
    ActivatorUsageItem, 
    MedicationPreferenceItem, 
    GenderDistributionItem, 
    TreatmentLocationDistributionItem,
    WeightLossRankingItem,
    WeightLossRankingResponse,
    WeightGainRankingItem,
    WeightGainRankingResponse,
    MedicationDosageItem,
    MedicationDosageResponse,
)
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

    # Média de idade dos pacientes
    birth_dates = db.query(Patient.birth_date).all()
    average_age = None
    if birth_dates:
        today = date.today()
        ages = []
        for (birth_date,) in birth_dates:
            age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
            ages.append(age)
        if ages:
            average_age = sum(ages) / len(ages)

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

    # Distribuição por gênero
    gender_distribution_raw: List[Tuple[str, int]] = (
        db.query(Patient.gender, func.count(Patient.id))
        .group_by(Patient.gender)
        .all()
    )
    
    # Garantir que sempre temos ambos os gêneros, mesmo que com count 0
    gender_counts = {gender.value: 0 for gender in GenderEnum}
    for gender, count in gender_distribution_raw:
        gender_counts[gender.value] = count
    
    gender_distribution = [
        GenderDistributionItem(
            gender="Masculino" if gender == GenderEnum.male.value else "Feminino",
            count=count
        )
        for gender, count in gender_counts.items()
    ]

    # Distribuição por local de atendimento
    treatment_location_distribution_raw: List[Tuple[str, int]] = (
        db.query(Patient.treatment_location, func.count(Patient.id))
        .group_by(Patient.treatment_location)
        .all()
    )
    
    # Garantir que sempre temos ambos os locais, mesmo que com count 0
    location_counts = {location.value: 0 for location in TreatmentLocationEnum}
    for location, count in treatment_location_distribution_raw:
        location_counts[location.value] = count
    
    treatment_location_distribution = [
        TreatmentLocationDistributionItem(
            location="Clínica" if location == TreatmentLocationEnum.clinic.value else "Domicílio",
            count=count
        )
        for location, count in location_counts.items()
    ]

    return DashboardStatsResponse(
        total_patients=total_patients,
        sessions_last_30_days=sessions_last_30_days,
        total_weight_lost_kg=float(total_weight_lost),
        average_age=round(average_age, 1) if average_age is not None else None,
        activators_usage=activators_usage,
        medications_preference=medications_preference,
        gender_distribution=gender_distribution,
        treatment_location_distribution=treatment_location_distribution,
    )


@router.get("/weight-loss-ranking", response_model=WeightLossRankingResponse)
async def get_weight_loss_ranking(
    start_date: Optional[date] = Query(None, description="Data inicial do período (formato: YYYY-MM-DD). Se não informado, usa últimos 30 dias."),
    end_date: Optional[date] = Query(None, description="Data final do período (formato: YYYY-MM-DD). Se não informado, usa data atual."),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Comentário em pt-BR: retorna ranking dos pacientes que mais perderam peso no período especificado.
    Se não informar datas, usa últimos 30 dias por padrão.
    """
    # Definir período padrão se não informado
    if end_date is None:
        end_date = date.today()
    
    if start_date is None:
        start_date = end_date - timedelta(days=30)
    
    # Converter para datetime para comparação com session_date
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())
    
    # Buscar pacientes que tiveram sessões no período
    patients_with_sessions_in_period = (
        db.query(Patient.id, Patient.name)
        .join(Cycle, Cycle.patient_id == Patient.id)
        .join(SessionModel, SessionModel.cycle_id == Cycle.id)
        .join(BodyComposition, BodyComposition.session_id == SessionModel.id)
        .filter(
            SessionModel.session_date >= start_datetime,
            SessionModel.session_date <= end_datetime
        )
        .distinct()
        .all()
    )
    
    ranking_items = []
    
    for patient_id, patient_name in patients_with_sessions_in_period:
        # Buscar primeira sessão no período
        first_session = (
            db.query(SessionModel)
            .join(Cycle, Cycle.id == SessionModel.cycle_id)
            .join(BodyComposition, BodyComposition.session_id == SessionModel.id)
            .options(joinedload(SessionModel.body_composition))
            .filter(
                Cycle.patient_id == patient_id,
                SessionModel.session_date >= start_datetime,
                SessionModel.session_date <= end_datetime
            )
            .order_by(SessionModel.session_date)
            .first()
        )
        
        # Buscar última sessão no período
        last_session = (
            db.query(SessionModel)
            .join(Cycle, Cycle.id == SessionModel.cycle_id)
            .join(BodyComposition, BodyComposition.session_id == SessionModel.id)
            .options(joinedload(SessionModel.body_composition))
            .filter(
                Cycle.patient_id == patient_id,
                SessionModel.session_date >= start_datetime,
                SessionModel.session_date <= end_datetime
            )
            .order_by(desc(SessionModel.session_date))
            .first()
        )
        
        if first_session and last_session:
            initial_weight = float(first_session.body_composition.weight_kg)
            final_weight = float(last_session.body_composition.weight_kg)
            weight_loss = initial_weight - final_weight  # Positivo = perdeu peso
            
            # Contar sessões no período
            sessions_count = (
                db.query(func.count(SessionModel.id))
                .join(Cycle, Cycle.id == SessionModel.cycle_id)
                .join(BodyComposition, BodyComposition.session_id == SessionModel.id)
                .filter(
                    Cycle.patient_id == patient_id,
                    SessionModel.session_date >= start_datetime,
                    SessionModel.session_date <= end_datetime
                )
                .scalar() or 0
            )
            
            ranking_items.append({
                "patient_id": patient_id,
                "patient_name": patient_name,
                "weight_loss_kg": round(weight_loss, 2),
                "initial_weight_kg": round(initial_weight, 2),
                "final_weight_kg": round(final_weight, 2),
                "sessions_count": sessions_count,
            })
    
    # Ordenar por maior perda de peso (descendente)
    ranking_items.sort(key=lambda x: x["weight_loss_kg"], reverse=True)
    
    # Adicionar rank
    ranked_items = [
        WeightLossRankingItem(
            rank=idx + 1,
            patient_id=item["patient_id"],
            patient_name=item["patient_name"],
            weight_loss_kg=item["weight_loss_kg"],
            initial_weight_kg=item["initial_weight_kg"],
            final_weight_kg=item["final_weight_kg"],
            sessions_count=item["sessions_count"],
        )
        for idx, item in enumerate(ranking_items)
    ]
    
    return WeightLossRankingResponse(
        items=ranked_items,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/weight-gain-ranking", response_model=WeightGainRankingResponse)
async def get_weight_gain_ranking(
    start_date: Optional[date] = Query(None, description="Data inicial do período (formato: YYYY-MM-DD). Se não informado, usa últimos 30 dias."),
    end_date: Optional[date] = Query(None, description="Data final do período (formato: YYYY-MM-DD). Se não informado, usa data atual."),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Comentário em pt-BR: retorna ranking dos pacientes que mais ganharam peso no período especificado.
    Se não informar datas, usa últimos 30 dias por padrão.
    """
    # Definir período padrão se não informado
    if end_date is None:
        end_date = date.today()
    
    if start_date is None:
        start_date = end_date - timedelta(days=30)
    
    # Converter para datetime para comparação com session_date
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())
    
    # Buscar pacientes que tiveram sessões no período
    patients_with_sessions_in_period = (
        db.query(Patient.id, Patient.name)
        .join(Cycle, Cycle.patient_id == Patient.id)
        .join(SessionModel, SessionModel.cycle_id == Cycle.id)
        .join(BodyComposition, BodyComposition.session_id == SessionModel.id)
        .filter(
            SessionModel.session_date >= start_datetime,
            SessionModel.session_date <= end_datetime
        )
        .distinct()
        .all()
    )
    
    ranking_items = []
    
    for patient_id, patient_name in patients_with_sessions_in_period:
        # Buscar primeira sessão no período
        first_session = (
            db.query(SessionModel)
            .join(Cycle, Cycle.id == SessionModel.cycle_id)
            .join(BodyComposition, BodyComposition.session_id == SessionModel.id)
            .options(joinedload(SessionModel.body_composition))
            .filter(
                Cycle.patient_id == patient_id,
                SessionModel.session_date >= start_datetime,
                SessionModel.session_date <= end_datetime
            )
            .order_by(SessionModel.session_date)
            .first()
        )
        
        # Buscar última sessão no período
        last_session = (
            db.query(SessionModel)
            .join(Cycle, Cycle.id == SessionModel.cycle_id)
            .join(BodyComposition, BodyComposition.session_id == SessionModel.id)
            .options(joinedload(SessionModel.body_composition))
            .filter(
                Cycle.patient_id == patient_id,
                SessionModel.session_date >= start_datetime,
                SessionModel.session_date <= end_datetime
            )
            .order_by(desc(SessionModel.session_date))
            .first()
        )
        
        if first_session and last_session:
            initial_weight = float(first_session.body_composition.weight_kg)
            final_weight = float(last_session.body_composition.weight_kg)
            weight_gain = final_weight - initial_weight  # Positivo = ganhou peso
            
            # Filtrar apenas pacientes que ganharam peso
            if weight_gain > 0:
                # Contar sessões no período
                sessions_count = (
                    db.query(func.count(SessionModel.id))
                    .join(Cycle, Cycle.id == SessionModel.cycle_id)
                    .join(BodyComposition, BodyComposition.session_id == SessionModel.id)
                    .filter(
                        Cycle.patient_id == patient_id,
                        SessionModel.session_date >= start_datetime,
                        SessionModel.session_date <= end_datetime
                    )
                    .scalar() or 0
                )
                
                ranking_items.append({
                    "patient_id": patient_id,
                    "patient_name": patient_name,
                    "weight_gain_kg": round(weight_gain, 2),
                    "initial_weight_kg": round(initial_weight, 2),
                    "final_weight_kg": round(final_weight, 2),
                    "sessions_count": sessions_count,
                })
    
    # Ordenar por maior ganho de peso (descendente)
    ranking_items.sort(key=lambda x: x["weight_gain_kg"], reverse=True)
    
    # Adicionar rank
    ranked_items = [
        WeightGainRankingItem(
            rank=idx + 1,
            patient_id=item["patient_id"],
            patient_name=item["patient_name"],
            weight_gain_kg=item["weight_gain_kg"],
            initial_weight_kg=item["initial_weight_kg"],
            final_weight_kg=item["final_weight_kg"],
            sessions_count=item["sessions_count"],
        )
        for idx, item in enumerate(ranking_items)
    ]
    
    return WeightGainRankingResponse(
        items=ranked_items,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/medication-dosage", response_model=MedicationDosageResponse)
async def get_medication_dosage(
    start_date: Optional[date] = Query(None, description="Data inicial do período (formato: YYYY-MM-DD). Se não informado, usa últimos 30 dias."),
    end_date: Optional[date] = Query(None, description="Data final do período (formato: YYYY-MM-DD). Se não informado, usa data atual."),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Comentário em pt-BR: retorna agrupamento de medicação e dosagem com quantidade de pacientes distintos que receberam aquela combinação no período especificado.
    Se não informar datas, usa últimos 30 dias por padrão.
    """
    # Definir período padrão se não informado
    if end_date is None:
        end_date = date.today()
    
    if start_date is None:
        start_date = end_date - timedelta(days=30)
    
    # Converter para datetime para comparação com session_date
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())
    
    # Agrupar por medicação e dosagem, contando pacientes distintos
    medication_dosage_raw: List[Tuple[str, Optional[Decimal], int]] = (
        db.query(
            Medication.name,
            SessionModel.dosage_mg,
            func.count(func.distinct(Cycle.patient_id))
        )
        .join(SessionModel, SessionModel.medication_id == Medication.id)
        .join(Cycle, Cycle.id == SessionModel.cycle_id)
        .filter(
            SessionModel.session_date >= start_datetime,
            SessionModel.session_date <= end_datetime,
            SessionModel.dosage_mg.isnot(None)
        )
        .group_by(Medication.id, Medication.name, SessionModel.dosage_mg)
        .order_by(Medication.name, SessionModel.dosage_mg)
        .all()
    )
    
    medication_dosage_items = [
        MedicationDosageItem(
            medication_name=medication_name,
            dosage_mg=float(dosage_mg) if dosage_mg is not None else 0.0,
            patients_count=patients_count,
        )
        for medication_name, dosage_mg, patients_count in medication_dosage_raw
    ]
    
    return MedicationDosageResponse(
        items=medication_dosage_items,
        start_date=start_date,
        end_date=end_date,
    )


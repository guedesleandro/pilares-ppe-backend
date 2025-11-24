from typing import List, Optional
from datetime import date
from pydantic import BaseModel
from uuid import UUID


class ActivatorUsageItem(BaseModel):
    """
    Comentário em pt-BR: item do gráfico de ativadores mais utilizados
    """
    name: str
    count: int


class MedicationPreferenceItem(BaseModel):
    """
    Comentário em pt-BR: item do gráfico de medicação preferencial mais optada
    """
    name: str
    count: int


class GenderDistributionItem(BaseModel):
    """
    Comentário em pt-BR: item do gráfico de distribuição por gênero
    """
    gender: str
    count: int


class TreatmentLocationDistributionItem(BaseModel):
    """
    Comentário em pt-BR: item do gráfico de distribuição por local de atendimento
    """
    location: str
    count: int


class WeightLossRankingItem(BaseModel):
    """
    Comentário em pt-BR: item do ranking de perda de peso
    """
    rank: int
    patient_id: UUID
    patient_name: str
    weight_loss_kg: float
    initial_weight_kg: float
    final_weight_kg: float
    sessions_count: int


class WeightLossRankingResponse(BaseModel):
    """
    Comentário em pt-BR: resposta do ranking de perda de peso
    """
    items: List[WeightLossRankingItem]
    start_date: Optional[date]
    end_date: Optional[date]


class WeightGainRankingItem(BaseModel):
    """
    Comentário em pt-BR: item do ranking de ganho de peso
    """
    rank: int
    patient_id: UUID
    patient_name: str
    weight_gain_kg: float
    initial_weight_kg: float
    final_weight_kg: float
    sessions_count: int


class WeightGainRankingResponse(BaseModel):
    """
    Comentário em pt-BR: resposta do ranking de ganho de peso
    """
    items: List[WeightGainRankingItem]
    start_date: Optional[date]
    end_date: Optional[date]


class MedicationDosageItem(BaseModel):
    """
    Comentário em pt-BR: item da tabela de medicação e dosagem
    """
    medication_name: str
    dosage_mg: float
    patients_count: int


class MedicationDosageResponse(BaseModel):
    """
    Comentário em pt-BR: resposta da tabela de medicação e dosagem
    """
    items: List[MedicationDosageItem]
    start_date: Optional[date]
    end_date: Optional[date]


class DashboardStatsResponse(BaseModel):
    """
    Comentário em pt-BR: estatísticas do dashboard com métricas e dados para gráficos
    """
    total_patients: int
    sessions_last_30_days: int
    total_weight_lost_kg: float
    average_age: float | None
    activators_usage: List[ActivatorUsageItem]
    medications_preference: List[MedicationPreferenceItem]
    gender_distribution: List[GenderDistributionItem]
    treatment_location_distribution: List[TreatmentLocationDistributionItem]


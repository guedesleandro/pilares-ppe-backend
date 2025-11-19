from typing import List
from pydantic import BaseModel


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


class DashboardStatsResponse(BaseModel):
    """
    Comentário em pt-BR: estatísticas do dashboard com métricas e dados para gráficos
    """
    total_patients: int
    sessions_last_30_days: int
    total_weight_lost_kg: float
    activators_usage: List[ActivatorUsageItem]
    medications_preference: List[MedicationPreferenceItem]


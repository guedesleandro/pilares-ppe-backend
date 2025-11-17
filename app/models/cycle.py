from sqlalchemy import Column, String, Integer, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.database import Base


class PeriodicityEnum(str, enum.Enum):
    """
    Enum para periodicidade do ciclo
    Usar: PeriodicityEnum.weekly, .biweekly ou .monthly no código
    """
    weekly = "weekly"
    biweekly = "biweekly"
    monthly = "monthly"


class CycleTypeEnum(str, enum.Enum):
    """
    Enum para tipo do ciclo
    Usar: CycleTypeEnum.normal ou .maintenance no código
    """
    normal = "normal"
    maintenance = "maintenance"


class Cycle(Base):
    __tablename__ = "cycles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    max_sessions = Column(Integer, nullable=False)
    periodicity = Column(Enum(PeriodicityEnum), nullable=False)
    type = Column(Enum(CycleTypeEnum), nullable=False, default=CycleTypeEnum.normal)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    patient = relationship("Patient", back_populates="cycles")
    sessions = relationship("Session", back_populates="cycle", cascade="all, delete-orphan")


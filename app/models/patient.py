from sqlalchemy import Column, String, Date, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.database import Base


class GenderEnum(str, enum.Enum):
    """
    Enum para gênero do paciente
    Usar: GenderEnum.male ou GenderEnum.female no código
    """
    male = "male"
    female = "female"


class TreatmentLocationEnum(str, enum.Enum):
    """
    Enum para localização do tratamento
    Usar: TreatmentLocationEnum.clinic ou TreatmentLocationEnum.home no código
    """
    clinic = "clinic"
    home = "home"


class PatientStatusEnum(str, enum.Enum):
    """
    Enum para status do paciente
    Usar: PatientStatusEnum.active, .inactive, etc no código
    """
    active = "active"
    inactive = "inactive"
    completed = "completed"


class Patient(Base):
    __tablename__ = "patients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    gender = Column(Enum(GenderEnum), nullable=False)
    birth_date = Column(Date, nullable=False)
    process_number = Column(String, nullable=True)
    treatment_location = Column(
        Enum(TreatmentLocationEnum),
        nullable=False,
        default=TreatmentLocationEnum.clinic
    )
    status = Column(
        Enum(PatientStatusEnum),
        nullable=False,
        default=PatientStatusEnum.active
    )
    preferred_medication_id = Column(
        UUID(as_uuid=True),
        ForeignKey("medications.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    cycles = relationship("Cycle", back_populates="patient", cascade="all, delete-orphan")
    preferred_medication = relationship("Medication", back_populates="preferred_by_patients")
    body_compositions = relationship(
        "BodyComposition",
        back_populates="patient",
        cascade="all, delete-orphan",
    )


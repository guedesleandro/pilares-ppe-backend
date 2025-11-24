from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base


class BodyComposition(Base):
    """
    Registro da composição corporal de um paciente por sessão.
    """

    __tablename__ = "body_compositions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    weight_kg = Column(Numeric(7, 2), nullable=False)
    fat_percentage = Column(Numeric(5, 2), nullable=False)
    fat_kg = Column(Numeric(7, 2), nullable=False)
    muscle_mass_percentage = Column(Numeric(5, 2), nullable=False)
    h2o_percentage = Column(Numeric(5, 2), nullable=False)
    metabolic_age = Column(Integer, nullable=False)
    visceral_fat = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relacionamentos
    patient = relationship("Patient", back_populates="body_compositions")
    session = relationship("Session", back_populates="body_composition", uselist=False)


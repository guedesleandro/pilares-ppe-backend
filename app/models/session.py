from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base


class Session(Base):
    __tablename__ = "sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cycle_id = Column(UUID(as_uuid=True), ForeignKey("cycles.id", ondelete="CASCADE"), nullable=False)
    medication_id = Column(
        UUID(as_uuid=True),
        ForeignKey("medications.id", ondelete="RESTRICT"),
        nullable=False,
    )
    activator_id = Column(
        UUID(as_uuid=True),
        ForeignKey("activators.id", ondelete="RESTRICT"),
        nullable=True,
    )
    dosage_mg = Column(Numeric(precision=10, scale=2), nullable=True)
    session_date = Column(DateTime(timezone=True), nullable=False)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    cycle = relationship("Cycle", back_populates="sessions")
    medication = relationship("Medication", back_populates="sessions")
    activator = relationship("Activator", back_populates="sessions")
    body_composition = relationship(
        "BodyComposition",
        back_populates="session",
        uselist=False,
        cascade="all, delete-orphan",
    )


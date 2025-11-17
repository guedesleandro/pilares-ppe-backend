from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base


class Medication(Base):
    """
    Medicação cadastrada no sistema
    """

    __tablename__ = "medications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    sessions = relationship(
        "Session",
        back_populates="medication",
    )
    preferred_by_patients = relationship(
        "Patient",
        back_populates="preferred_medication",
    )



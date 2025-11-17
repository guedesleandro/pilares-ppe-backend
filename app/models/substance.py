from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base


class Substance(Base):
    """
    Substância utilizada em compostos/ativadores metabólicos
    """

    __tablename__ = "substances"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    activator_compositions = relationship(
        "ActivatorComposition",
        back_populates="substance",
        cascade="all, delete-orphan",
    )



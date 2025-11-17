from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base


class Activator(Base):
    """
    Ativador metabólico (composto) que agrupa substâncias e volumes
    """

    __tablename__ = "activators"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    compositions = relationship(
        "ActivatorComposition",
        back_populates="activator",
        cascade="all, delete-orphan",
    )
    sessions = relationship(
        "Session",
        back_populates="activator",
    )



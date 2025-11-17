from sqlalchemy import Column, DateTime, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base


class ActivatorComposition(Base):
    """
    Linha de composição de um ativador metabólico
    """

    __tablename__ = "activator_compositions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    activator_id = Column(
        UUID(as_uuid=True),
        ForeignKey("activators.id", ondelete="CASCADE"),
        nullable=False,
    )
    substance_id = Column(
        UUID(as_uuid=True),
        ForeignKey("substances.id", ondelete="CASCADE"),
        nullable=False,
    )
    volume_ml = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    activator = relationship("Activator", back_populates="compositions")
    substance = relationship("Substance", back_populates="activator_compositions")



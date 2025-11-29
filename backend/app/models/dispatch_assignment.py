"""
DispatchAssignment Model - 派遣先割当 (Dispatch Assignment)

Simple model for grouping contracts.
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class DispatchAssignment(Base):
    """
    派遣先割当 - Dispatch Assignment grouping.

    Used to group related contracts together.
    """
    __tablename__ = "dispatch_assignments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    kobetsu_contracts = relationship("KobetsuKeiyakusho", back_populates="dispatch_assignment")

    def __repr__(self):
        return f"<DispatchAssignment {self.id}: {self.name}>"

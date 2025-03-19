"""
Workflow database model for BioinfoFlow.

This module defines the Workflow database model, representing workflow definitions.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import relationship

from ..config import Base


class Workflow(Base):
    """
    Workflow database model.
    
    Represents a workflow definition in the database.
    """
    
    __tablename__ = "workflows"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    version = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    yaml_content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow())
    
    # Relationships
    runs = relationship("Run", back_populates="workflow", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Workflow(id={self.id}, name='{self.name}', version='{self.version}')>" 
"""
Run database model for BioinfoFlow.

This module defines the Run database model, representing workflow executions.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from ..config import Base


class Run(Base):
    """
    Run database model.
    
    Represents a workflow execution run in the database.
    """
    
    __tablename__ = "runs"
    
    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False)
    run_id = Column(String(50), unique=True, nullable=False)
    status = Column(String(20), nullable=False)
    start_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    run_dir = Column(Text, nullable=False)
    inputs = Column(JSON, nullable=True)
    
    # Relationships
    workflow = relationship("Workflow", back_populates="runs")
    steps = relationship("Step", back_populates="run", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Run(id={self.id}, run_id='{self.run_id}', status='{self.status}')>" 
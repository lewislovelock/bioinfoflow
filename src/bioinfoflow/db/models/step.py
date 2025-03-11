"""
Step database model for BioinfoFlow.

This module defines the Step database model, representing workflow step executions.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from ..config import Base


class Step(Base):
    """
    Step database model.
    
    Represents a workflow step execution in the database.
    """
    
    __tablename__ = "steps"
    
    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("runs.id", ondelete="CASCADE"), nullable=False)
    step_name = Column(String(255), nullable=False)
    status = Column(String(20), nullable=False)
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    log_file = Column(Text, nullable=True)
    outputs = Column(JSON, nullable=True)
    
    # Relationships
    run = relationship("Run", back_populates="steps")
    
    def __repr__(self):
        return f"<Step(id={self.id}, step_name='{self.step_name}', status='{self.status}')>" 
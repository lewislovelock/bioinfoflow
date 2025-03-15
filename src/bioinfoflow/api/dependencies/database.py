"""
Database dependencies for BioinfoFlow API.

This module provides FastAPI dependencies for database access.
"""
from typing import Generator
from sqlalchemy.orm import Session

# Import database config and repositories
try:
    from bioinfoflow.db.config import db_config
    from bioinfoflow.db.repositories.workflow_repository import WorkflowRepository
    from bioinfoflow.db.repositories.run_repository import RunRepository
    from bioinfoflow.db.repositories.step_repository import StepRepository
    has_database = True
except ImportError:
    has_database = False


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency for getting a database session.
    
    Yields:
        A SQLAlchemy database session.
    """
    if not has_database:
        raise RuntimeError("Database module not available")
        
    db = db_config.get_session()
    try:
        yield db
    finally:
        db.close()


def get_workflow_repository(db: Session = None) -> WorkflowRepository:
    """
    Get the workflow repository.
    
    Args:
        db: Database session (optional, only for testing)
        
    Returns:
        WorkflowRepository instance
    """
    if not has_database:
        raise RuntimeError("Database module not available")
        
    if db is None:
        db = next(get_db())
        
    return WorkflowRepository(db)


def get_run_repository(db: Session = None) -> RunRepository:
    """
    Get the run repository.
    
    Args:
        db: Database session (optional, only for testing)
        
    Returns:
        RunRepository instance
    """
    if not has_database:
        raise RuntimeError("Database module not available")
        
    if db is None:
        db = next(get_db())
        
    return RunRepository(db)


def get_step_repository(db: Session = None) -> StepRepository:
    """
    Get the step repository.
    
    Args:
        db: Database session (optional, only for testing)
        
    Returns:
        StepRepository instance
    """
    if not has_database:
        raise RuntimeError("Database module not available")
        
    if db is None:
        db = next(get_db())
        
    return StepRepository(db) 
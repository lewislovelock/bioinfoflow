"""
Database configuration module for BioinfoFlow.

This module handles database connection settings and provides a SQLAlchemy engine.
"""
import os
from typing import Optional, Generator
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from loguru import logger

# SQLAlchemy base class for all models
Base = declarative_base()

# Default database URL
DEFAULT_DB_URL = "sqlite:///bioinfoflow.db"

class DatabaseConfig:
    """
    Database configuration class.
    
    Manages database connection settings and provides a SQLAlchemy engine.
    """
    
    def __init__(self, db_url: Optional[str] = None):
        """
        Initialize database configuration.
        
        Args:
            db_url: Database URL (defaults to environment variable or SQLite)
        """
        # Get database URL from environment variable or use default
        self.db_url = db_url or os.environ.get("BIOINFOFLOW_DB_URL", DEFAULT_DB_URL)
        
        # Create engine
        self.engine = create_engine(self.db_url)
        
        # Create session factory
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        logger.debug(f"Initialized database configuration with URL: {self.db_url}")
    
    def create_tables(self):
        """Create all tables in the database."""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Created database tables")
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            raise
    
    def get_session(self) -> Session:
        """
        Get a database session.
        
        Returns:
            New database session
        """
        return self.SessionLocal()


# Global database configuration
db_config = DatabaseConfig()


def get_db_session() -> Generator[Session, None, None]:
    """
    Get a new database session.
    
    This function is intended to be used as a dependency in FastAPI endpoints.
    
    Yields:
        Database session
    """
    session = db_config.get_session()
    try:
        yield session
    finally:
        session.close() 
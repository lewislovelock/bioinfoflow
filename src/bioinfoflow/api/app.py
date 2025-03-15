"""
FastAPI application for BioinfoFlow.

This module provides the main FastAPI application for BioinfoFlow API.
"""
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from bioinfoflow.api.dependencies import has_database
from bioinfoflow.api.routers import workflow_router, run_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager.
    
    Sets up and tears down resources for the API.
    """
    # Check database availability
    if not has_database:
        app.state.database_available = False
        logger.warning("Database module not available, some API features will be disabled")
    else:
        app.state.database_available = True
        logger.info("Database module available, all API features enabled")
    
    # Get base directory from environment if set
    base_dir = os.environ.get("BIOINFOFLOW_BASE_DIR")
    if base_dir:
        base_path = Path(base_dir)
        if base_path.exists() and base_path.is_dir():
            app.state.base_dir = base_dir
            logger.info(f"Using base directory: {base_dir}")
        else:
            logger.warning(f"Base directory {base_dir} not found or not a directory")
    
    yield
    
    logger.info("Shutting down API")


# Create FastAPI application
app = FastAPI(
    title="BioinfoFlow API",
    description="RESTful API for managing BioinfoFlow workflows",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development, should be restricted in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add API version prefix to all routes
api_prefix = "/api/v1"

# Include routers
app.include_router(workflow_router, prefix=api_prefix)
app.include_router(run_router, prefix=api_prefix)


@app.get("/api/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns the status of the API and its dependencies.
    """
    return {
        "status": "ok",
        "version": app.version,
        "database_available": getattr(app.state, "database_available", False)
    }


@app.get("/")
async def root():
    """
    Root endpoint that redirects to documentation.
    """
    return {"message": "Welcome to BioinfoFlow API", "docs_url": "/api/docs"} 
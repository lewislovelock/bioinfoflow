"""
Configuration dependencies for BioinfoFlow API.

This module provides FastAPI dependencies for configuration.
"""
from pathlib import Path
from typing import Optional
from functools import lru_cache

from bioinfoflow.core.config import Config


@lru_cache()
def get_config(base_dir: Optional[str] = None) -> Config:
    """
    Get BioinfoFlow configuration with caching.
    
    Args:
        base_dir: Optional base directory override
        
    Returns:
        Config instance
    """
    return Config(base_dir) 
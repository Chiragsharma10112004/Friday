"""
Re-export the unified Phase 6 Application Pipeline router for full backward compatibility.
"""
from app.api.application_pipeline import router, get_db

__all__ = ["router", "get_db"]
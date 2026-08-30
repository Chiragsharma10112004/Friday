from datetime import datetime, timezone
from fastapi import APIRouter
from app.config import APP_NAME, VERSION, ENV

router = APIRouter()

@router.get("/status")
def status():
    return {
        "assistant": APP_NAME,
        "version": VERSION,
        "environment": ENV,
        "status": "Online"
    }

@router.get("/health")
def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@router.get("/health/detailed")
def health_detailed():
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "application": APP_NAME,
        "version": VERSION,
        "environment": ENV
    }

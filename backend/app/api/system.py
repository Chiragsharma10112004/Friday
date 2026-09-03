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

@router.get("/health/readiness")
def health_readiness():
    from app.memory.database import SessionLocal
    db_status = "ready"
    try:
        db = SessionLocal()
        db.execute(__import__("sqlalchemy").text("SELECT 1"))
        db.close()
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return {
        "status": "ready" if db_status == "ready" else "degraded",
        "database": db_status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "application": APP_NAME,
        "version": VERSION,
    }

@router.get("/health/diagnostics")
def health_diagnostics():
    from app.core.self_healing.service import default_self_healing_service
    history = default_self_healing_service.get_audit_history()
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_self_healing_events": len(history),
        "recent_recovery_events": [h.dict() for h in history[:5]],
    }

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

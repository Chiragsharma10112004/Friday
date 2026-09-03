from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.memory.database import SessionLocal
from app.memory.repository import (
    get_all_memory,
    get_recent_messages,
    save_memory,
    delete_memory,
)

router = APIRouter(
    prefix="/memory",
    tags=["Memory"]
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class MemoryCreate(BaseModel):
    key: str
    value: str


@router.get("")
def list_memory(db: Session = Depends(get_db)):
    return get_all_memory(db)


@router.post("")
def create_memory(
    memory: MemoryCreate,
    db: Session = Depends(get_db)
):
    save_memory(db, memory.key, memory.value)

    return {
        "success": True,
        "key": memory.key,
        "value": memory.value
    }


@router.delete("/{key}")
def remove_memory(
    key: str,
    db: Session = Depends(get_db)
):
    return delete_memory(db, key)


@router.get("/history")
def memory_history(db: Session = Depends(get_db)):
    return get_recent_messages(db)

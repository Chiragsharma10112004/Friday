from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.memory.database import SessionLocal
from app.memory.repository import (
    get_all_memory,
    get_memory,
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


class MemoryItem(BaseModel):
    key: str
    value: str


class MemoryResponse(BaseModel):
    memories: Dict[str, str]
    total_count: int


class ChatHistoryItem(BaseModel):
    role: str
    content: str


@router.get("", response_model=MemoryResponse)
def list_memory(db: Session = Depends(get_db)):
    """Retrieve all permanent memory key-value pairs."""
    memories = get_all_memory(db)
    return MemoryResponse(
        memories=memories,
        total_count=len(memories)
    )


@router.get("/history", response_model=List[ChatHistoryItem])
def memory_history(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Retrieve recent conversation history in chronological order."""
    history = get_recent_messages(db, limit=limit)
    return [
        ChatHistoryItem(role=item["role"], content=item["content"])
        for item in history
    ]


@router.get("/{key}")
def get_single_memory(key: str, db: Session = Depends(get_db)):
    """Retrieve a single memory fact by key."""
    val = get_memory(db, key)
    if val is None:
        raise HTTPException(status_code=404, detail=f"Memory key '{key}' not found")
    return {"key": key, "value": val}


@router.post("", response_model=Dict[str, Any])
def create_or_update_memory(
    memory: MemoryItem,
    db: Session = Depends(get_db)
):
    """Save or update a permanent memory key-value pair."""
    key = memory.key.strip()
    value = memory.value.strip()
    if not key:
        raise HTTPException(status_code=400, detail="Key cannot be empty")

    save_memory(db, key, value)
    return {
        "success": True,
        "key": key,
        "value": value
    }


@router.delete("/{key}", response_model=Dict[str, Any])
def remove_memory(
    key: str,
    db: Session = Depends(get_db)
):
    """Delete a memory item by key."""
    deleted = delete_memory(db, key)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Memory key '{key}' not found")
    return {"success": True, "message": f"Memory key '{key}' deleted successfully"}

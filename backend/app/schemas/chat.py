from typing import Optional, List
from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str
    context_sources: Optional[List[str]] = None

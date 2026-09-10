from fastapi import APIRouter
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.ai_service import generate_response
from app.services.ai_service import generate_response_detailed

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("", response_model=ChatResponse)
@router.post("/", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    reply = generate_response(request.message)
    return ChatResponse(reply=reply)
    reply, context_sources = generate_response_detailed(request.message)
    return ChatResponse(reply=reply, context_sources=context_sources)

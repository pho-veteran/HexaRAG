from fastapi import APIRouter

from hexarag_api.models.chat import ChatRequest, ChatResponse
from hexarag_api.services.service_factory import get_chat_service

router = APIRouter()


@router.post('/chat', response_model=ChatResponse)
async def post_chat(request: ChatRequest) -> ChatResponse:
    return get_chat_service().answer(request.session_id, request.message)

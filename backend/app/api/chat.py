from fastapi import APIRouter

from app.api import fixtures
from app.api.schemas import ChatRequest, ChatResponse
from app.core.clock import resolve_at

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    return fixtures.chat(resolve_at(req.at))

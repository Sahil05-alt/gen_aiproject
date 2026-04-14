from typing import List, Optional

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from services.rag import ask, ask_stream

router = APIRouter()


class ChatRequest(BaseModel):
    """Chat request model."""
    question: str
    doc_ids: Optional[List[str]] = None
    top_k: int = 5
    stream: bool = False


class ChatResponse(BaseModel):
    """Chat response model."""
    answer: str
    citations: list
    confidence: float
    chunks_used: int
    model: str


@router.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat endpoint with RAG."""
    doc_ids = request.doc_ids or []
    result = ask(request.question, doc_ids, request.top_k)
    return ChatResponse(**result)


@router.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    """Streaming chat endpoint with RAG."""
    doc_ids = request.doc_ids or []

    async def generate():
        async for chunk in ask_stream(request.question, doc_ids, request.top_k):
            yield chunk

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache"
        }
    )

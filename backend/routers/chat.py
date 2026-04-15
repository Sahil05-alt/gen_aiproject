from typing import List, Optional

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from services.export_pdf import build_chat_pdf
from services.quiz import generate_quiz
from services.rag import ask, ask_stream, clear_session

router = APIRouter()


class ChatRequest(BaseModel):
    """Chat request model."""
    question: str
    session_id: str
    doc_ids: Optional[List[str]] = None
    top_k: int = 5
    stream: bool = False


class ClearHistoryRequest(BaseModel):
    """Clear chat history request model."""
    session_id: str


class ChatResponse(BaseModel):
    """Chat response model."""
    answer: str
    citations: list
    confidence: float
    chunks_used: int
    model: str


class CitationExport(BaseModel):
    """Citation data included in chat export payloads."""
    doc_name: str = "Unknown"
    chunk_index: int = 0
    excerpt: str = ""


class ExportMessage(BaseModel):
    """Chat message payload for PDF export."""
    role: str
    content: str
    confidence: Optional[float] = None
    citations: List[CitationExport] = Field(default_factory=list)


class ExportPdfRequest(BaseModel):
    """PDF export request model."""
    doc_title: str
    messages: List[ExportMessage]


class QuizRequest(BaseModel):
    """Quiz generation request model."""
    context: str
    num_questions: int


@router.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat endpoint with RAG."""
    doc_ids = request.doc_ids or []
    result = ask(request.question, doc_ids, request.top_k, request.session_id)
    return ChatResponse(**result)


@router.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    """Streaming chat endpoint with RAG."""
    doc_ids = request.doc_ids or []

    async def generate():
        async for chunk in ask_stream(request.question, doc_ids, request.top_k, request.session_id):
            yield chunk

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache"
        }
    )


@router.post("/api/clear-history")
async def clear_history(request: ClearHistoryRequest):
    """Clear the in-memory chat history for a session."""
    clear_session(request.session_id)
    return {"status": "cleared", "session_id": request.session_id}


@router.post("/api/export-pdf")
async def export_pdf(request: ExportPdfRequest):
    """Export the current chat transcript as a PDF."""
    pdf_buffer, filename = build_chat_pdf(
        request.doc_title,
        [message.model_dump() for message in request.messages],
    )

    return StreamingResponse(
        iter([pdf_buffer.getvalue()]),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@router.post("/api/generate-quiz")
async def generate_quiz_endpoint(request: QuizRequest):
    """Generate a multiple-choice quiz from retrieved context."""
    return generate_quiz(request.context, request.num_questions)

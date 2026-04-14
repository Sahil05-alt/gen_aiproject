from fastapi import APIRouter

from config import settings

router = APIRouter()


@router.get("/api/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "llm": "groq",
        "model": settings.groq_model,
        "embedding": "local/all-MiniLM-L6-v2",
        "vector_store": "faiss-local"
    }

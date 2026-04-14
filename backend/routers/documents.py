import uuid
from pathlib import Path
from typing import Dict, List

from fastapi import APIRouter, BackgroundTasks, File, UploadFile, HTTPException
from pydantic import BaseModel

from config import settings
from services.ingestion import ingest_document, delete_document

router = APIRouter()


# In-memory document registry
_doc_registry: Dict[str, "DocumentStatus"] = {}


class DocumentStatus(BaseModel):
    """Document processing status."""
    doc_id: str
    doc_name: str
    status: str = "processing"  # "processing" | "indexed" | "error"
    total_chunks: int = 0
    total_pages: int = 0
    error: str = None


SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}


def _process_document(file_path: str, doc_id: str, doc_name: str):
    """Background task to process a document."""
    try:
        result = ingest_document(file_path, doc_id, doc_name)
        _doc_registry[doc_id].status = "indexed"
        _doc_registry[doc_id].total_chunks = result["total_chunks"]
        _doc_registry[doc_id].total_pages = result["total_pages"]
    except Exception as e:
        _doc_registry[doc_id].status = "error"
        _doc_registry[doc_id].error = str(e)


@router.post("/api/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
):
    """Upload and process a document."""
    # Validate extension
    ext = Path(file.filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file extension: {ext}. Supported: {SUPPORTED_EXTENSIONS}"
        )

    # Generate unique ID and save file
    doc_id = str(uuid.uuid4())
    doc_name = file.filename
    save_path = Path(settings.uploads_path) / f"{doc_id}{ext}"

    contents = await file.read()
    with open(save_path, "wb") as f:
        f.write(contents)

    # Add to registry as processing
    _doc_registry[doc_id] = DocumentStatus(
        doc_id=doc_id,
        doc_name=doc_name,
        status="processing"
    )

    # Start background processing
    if background_tasks:
        background_tasks.add_task(_process_document, str(save_path), doc_id, doc_name)
    else:
        _process_document(str(save_path), doc_id, doc_name)

    return {"doc_id": doc_id, "doc_name": doc_name, "status": "processing"}


@router.get("/api/documents")
async def list_documents():
    """List all uploaded documents."""
    return list(_doc_registry.values())


@router.get("/api/documents/{doc_id}/status")
async def get_document_status(doc_id: str):
    """Get status of a specific document."""
    if doc_id not in _doc_registry:
        raise HTTPException(status_code=404, detail="Document not found")
    return _doc_registry[doc_id]


@router.delete("/api/documents/{doc_id}")
async def delete_document_endpoint(doc_id: str):
    """Delete a document and its vector index."""
    if doc_id not in _doc_registry:
        raise HTTPException(status_code=404, detail="Document not found")

    # Delete vector index
    delete_document(doc_id)

    # Remove from registry
    del _doc_registry[doc_id]

    return {"status": "deleted", "doc_id": doc_id}

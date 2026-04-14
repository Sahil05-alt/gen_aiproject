import shutil
from pathlib import Path
from typing import List, Optional

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader,
)
from langchain_community.vectorstores import FAISS
from langchain.schema import Document

from config import settings
from services.embeddings import get_embeddings


def get_loader(file_path: str):
    """Get the appropriate document loader based on file extension.

    Args:
        file_path: Path to the document file.

    Returns:
        A document loader instance.

    Raises:
        ValueError: If the file extension is not supported.
    """
    ext = Path(file_path).suffix.lower()
    if ext == ".pdf":
        return PyPDFLoader(file_path)
    elif ext == ".docx":
        return Docx2txtLoader(file_path)
    elif ext == ".txt":
        return TextLoader(file_path)
    else:
        raise ValueError(f"Unsupported file extension: {ext}")


def ingest_document(file_path: str, doc_id: str, doc_name: str) -> dict:
    """Ingest a document into the vector store.

    Args:
        file_path: Path to the document file.
        doc_id: Unique identifier for the document.
        doc_name: Human-readable name for the document.

    Returns:
        Dict with ingestion results: doc_id, doc_name, total_pages, total_chunks, status.
    """
    # Load the document
    loader = get_loader(file_path)
    pages = loader.load()
    total_pages = len(pages)

    # Split into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    chunks = text_splitter.split_documents(pages)

    # Enrich chunk metadata
    for i, chunk in enumerate(chunks):
        chunk.metadata["doc_id"] = doc_id
        chunk.metadata["doc_name"] = doc_name
        chunk.metadata["chunk_index"] = i
        chunk.metadata["total_chunks"] = len(chunks)
        chunk.metadata["source"] = file_path

    # Generate unique IDs for chunks
    ids = [f"{doc_id}_{i}" for i in range(len(chunks))]

    # Get embeddings
    embeddings = get_embeddings()

    # Create or overwrite FAISS index
    vector_store_path = Path(settings.vector_store_path) / doc_id
    if vector_store_path.exists():
        import shutil
        shutil.rmtree(str(vector_store_path))
    vector_store_path.mkdir(parents=True, exist_ok=True)
    FAISS.from_documents(chunks, embeddings, ids=ids).save_local(str(vector_store_path))

    return {
        "doc_id": doc_id,
        "doc_name": doc_name,
        "total_pages": total_pages,
        "total_chunks": len(chunks),
        "status": "indexed"
    }


def get_combined_retriever(doc_ids: List[str], top_k: int):
    """Get a combined retriever from multiple document indexes using MMR.

    Args:
        doc_ids: List of document IDs to retrieve from.
        top_k: Number of results to return.

    Returns:
        A retriever with MMR enabled.
    """
    # Avoid loading and merging the same FAISS index more than once.
    doc_ids = list(dict.fromkeys(doc_ids))

    embeddings = get_embeddings()
    vector_stores = []

    for doc_id in doc_ids:
        index_path = Path(settings.vector_store_path) / doc_id
        if index_path.exists():
            vector_store = FAISS.load_local(
                str(index_path),
                embeddings,
                allow_dangerous_deserialization=True
            )
            vector_stores.append(vector_store)

    if not vector_stores:
        return None

    if len(vector_stores) == 1:
        return vector_stores[0].as_retriever(
            search_type="mmr",
            search_kwargs={
                "k": top_k,
                "fetch_k": top_k * 3,
                "lambda_mult": 0.7
            }
        )

    # Merge multiple indexes
    combined = vector_stores[0]
    for vs in vector_stores[1:]:
        combined.merge_from(vs)

    return combined.as_retriever(
        search_type="mmr",
        search_kwargs={
            "k": top_k,
            "fetch_k": top_k * 3,
            "lambda_mult": 0.7
        }
    )


def delete_document(doc_id: str) -> bool:
    """Delete a document's vector index.

    Args:
        doc_id: The document ID to delete.

    Returns:
        True if deleted, False if not found.
    """
    index_path = Path(settings.vector_store_path) / doc_id
    if index_path.exists():
        shutil.rmtree(str(index_path))
        return True
    return False

import json
from typing import AsyncGenerator, Dict, List, Optional

from langchain.prompts import PromptTemplate
from langchain_groq import ChatGroq

from config import settings
from services.ingestion import get_combined_retriever


RAG_PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template="""You are DocMind, an AI assistant that answers questions based ONLY on the provided document context.
Rules: 1) Answer only from context — never hallucinate. 2) If the answer is not in the context, say 'I could not find relevant information in the uploaded documents.' 3) Cite sources inline as [DocName, chunk N]. 4) Use markdown for formatting (bold key terms, bullet lists).
CONTEXT: {context}
QUESTION: {question}
ANSWER:"""
)


def _format_source_docs(docs: List) -> List[Dict]:
    """Format documents as citation sources.

    Args:
        docs: List of LangChain documents.

    Returns:
        List of dicts with doc_name, doc_id, page, chunk_index, excerpt, source.
    """
    sources = []
    for doc in docs:
        excerpt = doc.page_content[:200] + "…" if len(doc.page_content) > 200 else doc.page_content
        sources.append({
            "doc_name": doc.metadata.get("doc_name", "Unknown"),
            "doc_id": doc.metadata.get("doc_id", ""),
            "page": doc.metadata.get("page", 0),
            "chunk_index": doc.metadata.get("chunk_index", 0),
            "excerpt": excerpt,
            "source": doc.metadata.get("source", "")
        })
    return sources


def _compute_confidence(docs: List, top_k: int) -> float:
    """Compute confidence score based on number of relevant chunks.

    Args:
        docs: List of retrieved documents.
        top_k: The requested top_k value.

    Returns:
        Confidence score as percentage (0-100).
    """
    return round(min(len(docs) / top_k, 1.0) * 100, 1)


def ask(question: str, doc_ids: List[str], top_k: int) -> Dict:
    """Ask a question using RAG.

    Args:
        question: The user's question.
        doc_ids: List of document IDs to search.
        top_k: Number of chunks to retrieve.

    Returns:
        Dict with answer, citations, confidence, chunks_used, model.
    """
    retriever = get_combined_retriever(doc_ids, top_k)
    if retriever is None:
        return {
            "answer": "I could not find relevant information in the uploaded documents.",
            "citations": [],
            "confidence": 0.0,
            "chunks_used": 0,
            "model": settings.groq_model
        }

    docs = retriever.get_relevant_documents(question)

    # Build context with source prefixes
    context_parts = []
    for doc in docs:
        doc_name = doc.metadata.get("doc_name", "Unknown")
        chunk_idx = doc.metadata.get("chunk_index", 0)
        context_parts.append(f"[{doc_name} | chunk {chunk_idx}]\n{doc.page_content}")

    context = "\n\n---\n\n".join(context_parts)

    # Create LLM
    llm = ChatGroq(
        model=settings.groq_model,
        groq_api_key=settings.groq_api_key,
        temperature=0.1,
        max_tokens=1024
    )

    # Invoke with prompt
    prompt = RAG_PROMPT.format(context=context, question=question)
    response = llm.invoke(prompt)
    answer = response.content

    citations = _format_source_docs(docs)
    confidence = _compute_confidence(docs, top_k)

    return {
        "answer": answer,
        "citations": citations,
        "confidence": confidence,
        "chunks_used": len(docs),
        "model": settings.groq_model
    }


async def ask_stream(question: str, doc_ids: List[str], top_k: int) -> AsyncGenerator[str, None]:
    """Ask a question using RAG with streaming response.

    Args:
        question: The user's question.
        doc_ids: List of document IDs to search.
        top_k: Number of chunks to retrieve.

    Yields:
        SSE-formatted events.
    """
    try:
        retriever = get_combined_retriever(doc_ids, top_k)
        if retriever is None:
            yield 'data: {"type":"meta","citations":[],"confidence":0}\n\n'
            yield 'data: {"type":"token","text":"I could not find relevant information in the uploaded documents."}\n\n'
            yield "data: [DONE]\n\n"
            return

        docs = retriever.get_relevant_documents(question)

        # Build context
        context_parts = []
        for doc in docs:
            doc_name = doc.metadata.get("doc_name", "Unknown")
            chunk_idx = doc.metadata.get("chunk_index", 0)
            context_parts.append(f"[{doc_name} | chunk {chunk_idx}]\n{doc.page_content}")

        context = "\n\n---\n\n".join(context_parts)

        # Format citations
        citations = _format_source_docs(docs)
        confidence = _compute_confidence(docs, top_k)

        # Emit meta event
        meta_event = {
            "type": "meta",
            "citations": citations,
            "confidence": confidence
        }
        yield f'data: {json.dumps(meta_event)}\n\n'

        # Create streaming LLM
        llm = ChatGroq(
            model=settings.groq_model,
            groq_api_key=settings.groq_api_key,
            temperature=0.1,
            max_tokens=1024,
            streaming=True
        )

        # Stream response
        prompt = RAG_PROMPT.format(context=context, question=question)
        async for chunk in llm.astream(prompt):
            token_event = {
                "type": "token",
                "text": chunk.content
            }
            yield f'data: {json.dumps(token_event)}\n\n'

        yield "data: [DONE]\n\n"

    except Exception as e:
        error_event = {
            "type": "error",
            "text": str(e)
        }
        yield f'data: {json.dumps(error_event)}\n\n'
        yield "data: [DONE]\n\n"

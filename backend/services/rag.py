import json
from typing import AsyncGenerator, Dict, List

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from config import settings
from services.ingestion import get_combined_retriever


SESSIONS: Dict[str, List[Dict[str, str]]] = {}
MAX_SESSION_MESSAGES = 20
NO_CONTEXT_ANSWER = "I could not find relevant information in the uploaded documents."

RAG_SYSTEM_PROMPT = """You are DocMind, an AI assistant that answers questions based ONLY on the provided document context.
Rules:
1) Answer only from context and the conversation history. Never hallucinate.
2) If the answer is not in the context, say 'I could not find relevant information in the uploaded documents.'
3) Cite sources inline as [DocName, chunk N].
4) Use markdown for formatting, including bold key terms and bullet lists.

CONTEXT:
{context}"""


def _format_source_docs(docs: List) -> List[Dict]:
    """Format documents as citation sources."""
    sources = []
    for doc in docs:
        excerpt = doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
        sources.append({
            "doc_name": doc.metadata.get("doc_name", "Unknown"),
            "doc_id": doc.metadata.get("doc_id", ""),
            "page": doc.metadata.get("page", 0),
            "chunk_index": doc.metadata.get("chunk_index", 0),
            "excerpt": excerpt,
            "source": doc.metadata.get("source", ""),
        })
    return sources


def _compute_confidence(docs: List, top_k: int) -> float:
    """Compute confidence score based on number of relevant chunks."""
    return round(min(len(docs) / top_k, 1.0) * 100, 1)


def _get_session_history(session_id: str) -> List[Dict[str, str]]:
    """Return a shallow copy of the in-memory session history."""
    return list(SESSIONS.get(session_id, []))


def save_turn(session_id: str, user_msg: str, answer: str):
    """Append a user/assistant turn and retain only the latest messages."""
    history = SESSIONS.setdefault(session_id, [])
    history.extend([
        {"role": "user", "content": user_msg},
        {"role": "assistant", "content": answer},
    ])
    SESSIONS[session_id] = history[-MAX_SESSION_MESSAGES:]


def clear_session(session_id: str):
    """Delete all stored history for a session."""
    SESSIONS.pop(session_id, None)


def _build_context(docs: List) -> str:
    """Build the retriever context string for the LLM."""
    context_parts = []
    for doc in docs:
        doc_name = doc.metadata.get("doc_name", "Unknown")
        chunk_idx = doc.metadata.get("chunk_index", 0)
        context_parts.append(f"[{doc_name} | chunk {chunk_idx}]\n{doc.page_content}")
    return "\n\n---\n\n".join(context_parts)


def _build_messages(session_id: str, context: str, question: str) -> List:
    """Compose the system message, prior history, and current user question."""
    messages = [SystemMessage(content=RAG_SYSTEM_PROMPT.format(context=context))]

    for turn in _get_session_history(session_id):
        if turn["role"] == "user":
            messages.append(HumanMessage(content=turn["content"]))
        elif turn["role"] == "assistant":
            messages.append(AIMessage(content=turn["content"]))

    messages.append(HumanMessage(content=question))
    return messages


def ask(question: str, doc_ids: List[str], top_k: int, session_id: str) -> Dict:
    """Ask a question using RAG with prior session history."""
    retriever = get_combined_retriever(doc_ids, top_k)
    if retriever is None:
        save_turn(session_id, question, NO_CONTEXT_ANSWER)
        return {
            "answer": NO_CONTEXT_ANSWER,
            "citations": [],
            "confidence": 0.0,
            "chunks_used": 0,
            "model": settings.groq_model,
        }

    docs = retriever.invoke(question)
    context = _build_context(docs)

    llm = ChatGroq(
        model=settings.groq_model,
        groq_api_key=settings.groq_api_key,
        temperature=0.1,
        max_tokens=1024,
    )

    response = llm.invoke(_build_messages(session_id, context, question))
    answer = response.content
    save_turn(session_id, question, answer)

    citations = _format_source_docs(docs)
    confidence = _compute_confidence(docs, top_k)

    return {
        "answer": answer,
        "citations": citations,
        "confidence": confidence,
        "chunks_used": len(docs),
        "model": settings.groq_model,
    }


async def ask_stream(
    question: str,
    doc_ids: List[str],
    top_k: int,
    session_id: str,
) -> AsyncGenerator[str, None]:
    """Ask a question using RAG with streaming response and session memory."""
    try:
        retriever = get_combined_retriever(doc_ids, top_k)
        if retriever is None:
            save_turn(session_id, question, NO_CONTEXT_ANSWER)
            yield 'data: {"type":"meta","citations":[],"confidence":0}\n\n'
            yield f'data: {json.dumps({"type": "token", "text": NO_CONTEXT_ANSWER})}\n\n'
            yield "data: [DONE]\n\n"
            return

        docs = retriever.invoke(question)
        context = _build_context(docs)
        citations = _format_source_docs(docs)
        confidence = _compute_confidence(docs, top_k)

        meta_event = {
            "type": "meta",
            "citations": citations,
            "confidence": confidence,
        }
        yield f'data: {json.dumps(meta_event)}\n\n'

        llm = ChatGroq(
            model=settings.groq_model,
            groq_api_key=settings.groq_api_key,
            temperature=0.1,
            max_tokens=1024,
            streaming=True,
        )

        answer_parts = []
        async for chunk in llm.astream(_build_messages(session_id, context, question)):
            answer_parts.append(chunk.content)
            token_event = {
                "type": "token",
                "text": chunk.content,
            }
            yield f'data: {json.dumps(token_event)}\n\n'

        save_turn(session_id, question, "".join(answer_parts))
        yield "data: [DONE]\n\n"

    except Exception as e:
        error_event = {
            "type": "error",
            "text": str(e),
        }
        yield f'data: {json.dumps(error_event)}\n\n'
        yield "data: [DONE]\n\n"

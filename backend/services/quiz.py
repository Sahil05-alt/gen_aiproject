import json
from typing import Any, Dict

from langchain_groq import ChatGroq

from config import settings


QUIZ_SYSTEM_PROMPT = (
    "Respond ONLY with valid JSON, no markdown. "
    "Format: {questions: [{question, options: [{label, text}], answer, explanation}]}"
)

QUIZ_USER_PROMPT = """Create {num_questions} multiple-choice questions from the supplied context.

Rules:
- Use only the supplied context.
- Each question must have exactly 4 options labeled A, B, C, D.
- The answer field must be the correct option label.
- Keep explanations concise and grounded in the context.
- Return strict JSON only.

Context:
{context}
"""


def generate_quiz(context: str, num_questions: int) -> Dict[str, Any]:
    """Generate quiz JSON from document context."""
    llm = ChatGroq(
        model=settings.groq_model,
        groq_api_key=settings.groq_api_key,
        temperature=0.2,
        max_tokens=1800,
    )

    response = llm.invoke([
        {"role": "system", "content": QUIZ_SYSTEM_PROMPT},
        {"role": "user", "content": QUIZ_USER_PROMPT.format(context=context, num_questions=num_questions)},
    ])

    content = response.content.strip()
    quiz = json.loads(content)

    questions = quiz.get("questions")
    if not isinstance(questions, list):
        raise ValueError("Invalid quiz format returned by model.")

    normalized_questions = []
    for item in questions:
        options = item.get("options", [])
        if len(options) != 4:
            raise ValueError("Each quiz question must include exactly 4 options.")

        normalized_questions.append({
            "question": item.get("question", "").strip(),
            "options": [
                {
                    "label": option.get("label", "").strip(),
                    "text": option.get("text", "").strip(),
                }
                for option in options
            ],
            "answer": item.get("answer", "").strip(),
            "explanation": item.get("explanation", "").strip(),
        })

    return {"questions": normalized_questions}

def build_quiz_prompt(
    context: str,
    count: int,
    question_type: str,
    difficulty: str,
    topic: str | None,
    exclude_questions: list[str],
) -> str:
    type_instructions = {
        "mcq": (
            'Each question must have exactly 4 options labeled A, B, C, D. '
            'correct_answer must be exactly "A", "B", "C", or "D".'
        ),
        "true_false": (
            'options must be ["True", "False"]. '
            'correct_answer must be exactly "True" or "False".'
        ),
        "fill_in_the_blank": (
            "The question must contain a blank shown as ___. "
            "options must be null. correct_answer is the exact word or phrase that fills the blank."
        ),
    }

    exclude_text = ""
    if exclude_questions:
        items = "\n".join(f"- {q}" for q in exclude_questions[:20])
        exclude_text = f"\nDo NOT repeat or closely resemble these existing questions:\n{items}\n"

    topic_text = f"\nFocus specifically on this topic: {topic}" if topic else ""

    difficulty_guidance = {
        "easy": "Use straightforward recall questions based on explicitly stated facts.",
        "medium": "Mix recall and comprehension — require understanding, not just memorization.",
        "hard": "Require inference, analysis, or synthesis across multiple parts of the document.",
    }.get(difficulty, "")

    return f"""You are an expert quiz generator. Generate {count} quiz questions from the document content below.

Question type: {question_type}
Rules for this type: {type_instructions.get(question_type, "")}

Difficulty: {difficulty}
Difficulty guidance: {difficulty_guidance}
{topic_text}
{exclude_text}

DOCUMENT CONTENT:
{context}

Return ONLY valid JSON — no markdown, no backticks, no explanation outside the JSON.

{{
  "questions": [
    {{
      "question_text": "...",
      "question_type": "{question_type}",
      "difficulty": "{difficulty}",
      "options": ["A. ...", "B. ...", "C. ...", "D. ..."] or null,
      "correct_answer": "...",
      "explanation": "Brief explanation of why this answer is correct.",
      "source_page": 1
    }}
  ]
}}"""
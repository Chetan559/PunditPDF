def build_evaluation_prompt(qa_pairs: list[dict]) -> str:
    """
    Build prompt for LLM to evaluate submitted quiz answers.
    qa_pairs: list of { question_id, question_text, question_type,
                        correct_answer, user_answer, explanation }
    """
    qa_text = "\n\n".join([
        f"Q{i + 1} [ID: {qa['question_id']}]\n"
        f"Type: {qa['question_type']}\n"
        f"Question: {qa['question_text']}\n"
        f"Correct Answer: {qa['correct_answer']}\n"
        f"User Answer: {qa.get('user_answer') or '(no answer provided)'}"
        for i, qa in enumerate(qa_pairs)
    ])

    return f"""You are a strict but fair quiz evaluator. Evaluate the following quiz attempt.

Grading rules:
- For MCQ: user_answer must match the option label exactly (A/B/C/D) — case-insensitive.
- For true_false: must match "True" or "False" — case-insensitive.
- For fill_in_the_blank: accept minor spelling variations and synonyms, but the core meaning must match.
- If user_answer is empty or null, mark as incorrect.

QUIZ ANSWERS TO EVALUATE:
{qa_text}

Return ONLY valid JSON — no markdown, no backticks, no text outside the JSON.

{{
  "per_question": [
    {{
      "question_id": "exact id from above",
      "is_correct": true,
      "explanation": "Why this is correct or incorrect, referencing the right answer."
    }}
  ],
  "weak_topics": ["topic1", "topic2"],
  "recommendation": "Specific, actionable advice on what to review based on the mistakes made."
}}"""


def build_recommendation_prompt(
    weak_topics: list[str],
    pdf_summary: str,
    percentage: float,
    grade: str,
) -> str:
    """
    Build prompt for deeper, personalized study recommendations.
    Called separately from grading — used by recommendation_service.
    """
    topics_text = ", ".join(weak_topics) if weak_topics else "none identified"

    return f"""A student just completed a quiz on a document and scored {percentage}% (Grade: {grade}).

Weak topics identified: {topics_text}

Document summary:
{pdf_summary}

Write a concise, encouraging, and specific study plan for this student.
Include:
1. Which sections of the document to re-read
2. What concepts to focus on
3. One practical tip for retention

Keep it under 150 words. Be direct and supportive.
Return ONLY the recommendation text — no JSON, no headers."""
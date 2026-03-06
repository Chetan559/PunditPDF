def build_rag_prompt(question: str, chunks: list[dict], history: list[dict]) -> str:
    """
    Build the full RAG prompt sent to Gemini.

    chunks: [{text, page_number, score, ...}]
    history: [{"role": "user"|"assistant", "content": "..."}]
    """
    # Format context chunks
    context_parts = []
    for i, chunk in enumerate(chunks):
        context_parts.append(
            f"[Source {i + 1} — Page {chunk['page_number']}]\n{chunk['text']}"
        )
    context = "\n\n".join(context_parts)

    # Format recent history (exclude current question)
    history_text = ""
    if history:
        lines = []
        for m in history[-6:]:  # last 3 exchanges
            role = "User" if m["role"] == "user" else "Assistant"
            lines.append(f"{role}: {m['content']}")
        history_text = "\n".join(lines)

    prompt = f"""You are a helpful assistant answering questions about a document.
Use ONLY the provided context to answer. If the answer is not in the context, say so clearly.
Be concise and precise. Reference page numbers when relevant.

{"--- Conversation History ---" if history_text else ""}
{history_text}

--- Document Context ---
{context}

--- Question ---
{question}

--- Answer ---"""

    return prompt


def build_continuation_prompt(message: str, history: list[dict]) -> list[dict]:
    """
    For continuation messages, return history formatted for multi-turn LLM call.
    No RAG context needed — model uses conversation history only.
    """
    messages = list(history)
    messages.append({"role": "user", "content": message})
    return messages
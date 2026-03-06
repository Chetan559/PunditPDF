from loguru import logger

CONTINUATION_SIGNALS = {
    "yes", "no", "ok", "okay", "sure", "go ahead", "do it", "continue",
    "tell me more", "elaborate", "please", "yep", "nope", "alright",
    "go on", "more", "expand", "explain further", "and", "why", "when",
    "show me", "what else", "proceed", "sounds good",
}


class IntentService:

    async def detect(self, message: str, history: list[dict]) -> str:
        """
        Returns 'rag' or 'continuation'.

        Priority:
        1. No history → always rag
        2. Long message (>10 words) → always rag
        3. Keyword match → continuation
        4. Short ambiguous message → ask LLM
        """
        if not history:
            return "rag"

        normalized = message.lower().strip().rstrip(".!?")

        if len(message.split()) > 10:
            return "rag"

        if normalized in CONTINUATION_SIGNALS:
            logger.debug(f"Intent: continuation (keyword) — '{message}'")
            return "continuation"

        # Ambiguous short message — ask LLM
        return await self._llm_classify(message, history)

    async def _llm_classify(self, message: str, history: list[dict]) -> str:
        from app.services.llm_service import llm_service

        recent = history[-3:]
        history_text = "\n".join(
            f"{'User' if m['role'] == 'user' else 'Assistant'}: {m['content'][:120]}"
            for m in recent
        )

        prompt = f"""Recent conversation:
{history_text}

New message: "{message}"

Is this a follow-up to the conversation above, or a completely new question about the document?
Reply with ONLY one word: continuation OR rag"""

        try:
            result = await llm_service.generate(prompt, lite=True)
            intent = "continuation" if "continuation" in result.strip().lower() else "rag"
            logger.debug(f"Intent: {intent} (LLM) — '{message}'")
            return intent
        except Exception as e:
            logger.warning(f"Intent LLM failed, defaulting to rag: {e}")
            return "rag"


intent_service = IntentService()
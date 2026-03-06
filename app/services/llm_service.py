from groq import AsyncGroq
from loguru import logger
from app.core.config import get_settings

settings = get_settings()

CONTINUATION_SIGNALS = {
    "yes", "no", "go ahead", "sure", "do it", "continue", "tell me more",
    "elaborate", "okay", "ok", "proceed", "please", "yep", "nope", "alright",
    "sounds good", "go on", "more", "expand", "explain", "and", "why", "when",
}

# Models
MODEL_MAIN   = "llama-3.3-70b-versatile"   # RAG answers, chat, follow-ups
MODEL_FAST   = "llama-3.1-8b-instant"      # Intent detection (cheap + fast)


class LLMService:
    def __init__(self):
        self._groq = AsyncGroq(api_key=settings.GROQ_API_KEY)

    async def _call(
        self,
        messages: list[dict],
        model: str = MODEL_MAIN,
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> str:
        response = await self._groq.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content

    # ── Main generation ───────────────────────────────────────────────────────

    async def generate(self, prompt: str, lite: bool = False) -> str:
        """Single-turn generation — used for RAG answers."""
        try:
            model = MODEL_FAST if lite else MODEL_MAIN
            return await self._call(
                messages=[{"role": "user", "content": prompt}],
                model=model,
            )
        except Exception as e:
            logger.error(f"Groq generate error: {e}")
            raise

    async def generate_with_history(self, messages: list[dict], system: str = "") -> str:
        """Multi-turn generation — used for continuation mode."""
        try:
            full = []
            if system:
                full.append({"role": "system", "content": system})
            # Groq uses "assistant" not "model"
            for m in messages:
                full.append({"role": m["role"], "content": m["content"]})
            return await self._call(messages=full)
        except Exception as e:
            logger.error(f"Groq chat error: {e}")
            raise

    async def generate_groq(self, prompt: str, system: str = "") -> str:
        """Structured JSON output — used for quiz generation."""
        try:
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})
            return await self._call(messages=messages, temperature=0.2, max_tokens=2048)
        except Exception as e:
            logger.error(f"Groq structured error: {e}")
            raise

    # ── Intent detection ──────────────────────────────────────────────────────

    async def detect_intent(self, message: str, history: list[dict]) -> str:
        normalized = message.lower().strip().rstrip(".!?")

        if normalized in CONTINUATION_SIGNALS:
            logger.debug(f"Intent: continuation (keyword) — '{message}'")
            return "continuation"

        if not history or len(message.split()) > 10:
            return "new_question"

        recent = history[-3:]
        history_text = "\n".join([f"{m['role'].upper()}: {m['content'][:100]}" for m in recent])
        prompt = f"""Conversation so far:
{history_text}

New message: "{message}"

Is this a follow-up/continuation of the conversation, or a completely new question?
Reply with ONLY one word: continuation OR new_question"""

        try:
            result = await self._call(
                messages=[{"role": "user", "content": prompt}],
                model=MODEL_FAST,
                max_tokens=5,
            )
            intent = "continuation" if "continuation" in result.strip().lower() else "new_question"
            logger.debug(f"Intent: {intent} (LLM) — '{message}'")
            return intent
        except Exception as e:
            logger.warning(f"Intent detection failed, defaulting to new_question: {e}")
            return "new_question"

    # ── Follow-up generation ──────────────────────────────────────────────────

    async def generate_follow_up(self, answer: str) -> str:
        prompt = f"""Based on this answer:

{answer}

Suggest 1 short, natural follow-up question the user might want to ask next.
Return ONLY the question, no preamble."""
        try:
            return await self._call(
                messages=[{"role": "user", "content": prompt}],
                model=MODEL_FAST,
                max_tokens=60,
            )
        except Exception as e:
            logger.warning(f"Follow-up generation failed: {e}")
            return ""


llm_service = LLMService()
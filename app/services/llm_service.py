import google.generativeai as genai
from groq import AsyncGroq
from loguru import logger
from app.core.config import get_settings

settings = get_settings()

genai.configure(api_key=settings.GEMINI_API_KEY)

# Continuation signals — checked before hitting LLM for intent detection
CONTINUATION_SIGNALS = {
    "yes", "no", "go ahead", "sure", "do it", "continue", "tell me more",
    "elaborate", "okay", "ok", "proceed", "please", "yep", "nope", "alright",
    "sounds good", "go on", "more", "expand", "explain", "and", "why", "when",
}


class LLMService:
    def __init__(self):
        self._flash = genai.GenerativeModel("gemini-2.0-flash")
        self._flash_lite = genai.GenerativeModel("gemini-2.0-flash-lite")
        self._groq = AsyncGroq(api_key=settings.GROQ_API_KEY)

    # ── Gemini ────────────────────────────────────────────────────────────────

    async def generate(self, prompt: str, lite: bool = False) -> str:
        """Single-turn generation with Gemini Flash."""
        try:
            model = self._flash_lite if lite else self._flash
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Gemini generate error: {e}")
            raise

    async def generate_with_history(self, messages: list[dict], system: str = "") -> str:
        """
        Multi-turn generation with Gemini using conversation history.
        messages: [{"role": "user"|"assistant", "content": "..."}]
        """
        try:
            history = []
            for msg in messages[:-1]:
                role = "user" if msg["role"] == "user" else "model"
                history.append({"role": role, "parts": [msg["content"]]})

            chat = self._flash.start_chat(history=history)
            last = messages[-1]["content"]
            if system:
                last = f"{system}\n\n{last}"
            response = chat.send_message(last)
            return response.text
        except Exception as e:
            logger.error(f"Gemini chat error: {e}")
            raise

    # ── Groq ──────────────────────────────────────────────────────────────────

    async def generate_groq(self, prompt: str, system: str = "") -> str:
        """
        Generation with Groq Llama 3.3 70B.
        Use for structured JSON output (quiz generation, evaluation).
        """
        try:
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})

            response = await self._groq.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                temperature=0.3,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq generate error: {e}")
            raise

    # ── Intent detection ──────────────────────────────────────────────────────

    async def detect_intent(self, message: str, history: list[dict]) -> str:
        """
        Returns 'continuation' or 'new_question'.

        Flow:
        1. Keyword match (free, instant)
        2. Long message → always new_question
        3. No history → always new_question
        4. Ambiguous short message → ask Gemini Lite
        """
        normalized = message.lower().strip().rstrip(".!?")

        if normalized in CONTINUATION_SIGNALS:
            logger.debug(f"Intent: continuation (keyword) — '{message}'")
            return "continuation"

        if not history or len(message.split()) > 10:
            return "new_question"

        # Ambiguous — ask LLM
        recent = history[-3:]
        history_text = "\n".join([f"{m['role'].upper()}: {m['content'][:100]}" for m in recent])
        prompt = f"""Conversation so far:
{history_text}

New message: "{message}"

Is this a follow-up/continuation of the conversation, or a completely new question?
Reply with ONLY one word: continuation OR new_question"""

        try:
            result = await self.generate(prompt, lite=True)
            intent = "continuation" if "continuation" in result.strip().lower() else "new_question"
            logger.debug(f"Intent: {intent} (LLM) — '{message}'")
            return intent
        except Exception as e:
            logger.warning(f"Intent detection failed, defaulting to new_question: {e}")
            return "new_question"

    # ── Follow-up generation ──────────────────────────────────────────────────

    async def generate_follow_up(self, answer: str) -> str:
        """Generate a single follow-up question based on the answer."""
        prompt = f"""Based on this answer:

{answer}

Suggest 1 short, natural follow-up question the user might want to ask next.
Return ONLY the question. No preamble, no explanation."""
        try:
            return await self.generate(prompt, lite=True)
        except Exception as e:
            logger.warning(f"Follow-up generation failed: {e}")
            return ""


llm_service = LLMService()
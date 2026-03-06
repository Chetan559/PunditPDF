from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None   # null = start new session
    user_id: str = "default_user"
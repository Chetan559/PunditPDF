from pydantic import BaseModel


class UploadQueryParams(BaseModel):
    user_id: str = "default_user"
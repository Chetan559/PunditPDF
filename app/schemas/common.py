from pydantic import BaseModel


class BBox(BaseModel):
    x0: float
    y0: float
    x1: float
    y1: float


class SuccessResponse(BaseModel):
    success: bool = True
    message: str
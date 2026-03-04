from pydantic import BaseModel
from datetime import datetime


class UploadResponse(BaseModel):
    id: str
    name: str
    status: str
    message: str = "Upload successful. Processing started."


class PDFStatusResponse(BaseModel):
    id: str
    name: str
    status: str          # queued | processing | ready | failed
    progress: int        # 0-100
    message: str | None
    pdf_type: str | None
    total_pages: int | None


class PDFMetaResponse(BaseModel):
    id: str
    name: str
    file_size: int | None
    total_pages: int | None
    pdf_type: str | None
    ocr_applied: bool
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class PDFListResponse(BaseModel):
    pdfs: list[PDFMetaResponse]
    total: int
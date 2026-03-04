from fastapi import APIRouter, Depends, UploadFile, File, BackgroundTasks, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.document.document_service import document_service
from app.schemas.document.response import (
    UploadResponse, PDFStatusResponse, PDFMetaResponse, PDFListResponse
)

router = APIRouter(prefix="/api/documents", tags=["Documents"])


@router.post("/upload", response_model=UploadResponse, status_code=201)
async def upload_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user_id: str = Query(default="default_user"),
    db: AsyncSession = Depends(get_db),
):
    return await document_service.upload(db, file, user_id, background_tasks)


@router.get("/", response_model=PDFListResponse)
async def list_pdfs(
    user_id: str = Query(default="default_user"),
    db: AsyncSession = Depends(get_db),
):
    return await document_service.list_by_user(db, user_id)


@router.get("/{pdf_id}/status", response_model=PDFStatusResponse)
async def get_status(pdf_id: str, db: AsyncSession = Depends(get_db)):
    return await document_service.get_status(db, pdf_id)


@router.get("/{pdf_id}", response_model=PDFMetaResponse)
async def get_meta(pdf_id: str, db: AsyncSession = Depends(get_db)):
    return await document_service.get_meta(db, pdf_id)


@router.get("/{pdf_id}/file", response_class=FileResponse)
async def get_file(pdf_id: str, db: AsyncSession = Depends(get_db)):
    """Serves the raw PDF — consumed by react-pdf viewer on the frontend"""
    file_path = await document_service.get_file_path(db, pdf_id)
    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=f"{pdf_id}.pdf",
    )


@router.delete("/{pdf_id}", status_code=204)
async def delete_pdf(pdf_id: str, db: AsyncSession = Depends(get_db)):
    await document_service.delete(db, pdf_id)
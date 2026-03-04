import os
import uuid
import aiofiles
from fastapi import UploadFile, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.core.config import get_settings
from app.core.exceptions import PDFNotFoundError, FileTooLargeError, InvalidFileTypeError
from app.repos.document.document_repo import document_repo
from app.services.document.indexing_service import indexing_service
from app.services.document.ingestion_service import (
    detect_pdf_type, run_ocr, extract_chunks, get_page_count
)

settings = get_settings()

STATUS_PROGRESS = {
    "queued":     0,
    "processing": 40,
    "ready":      100,
    "failed":     0,
}


class DocumentService:

    async def upload(
        self,
        db: AsyncSession,
        file: UploadFile,
        user_id: str,
        background_tasks: BackgroundTasks,
    ) -> dict:
        self._validate_file(file)

        content = await file.read()
        if len(content) > settings.max_file_size_bytes:
            raise FileTooLargeError(settings.MAX_FILE_SIZE_MB)

        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        pdf_id = str(uuid.uuid4())
        file_path = os.path.join(settings.UPLOAD_DIR, f"{pdf_id}.pdf")

        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)

        pdf = await document_repo.create(db, {
            "id": pdf_id,
            "user_id": user_id,
            "name": file.filename,
            "file_path": file_path,
            "file_size": len(content),
            "status": "queued",
        })
        await db.commit()

        background_tasks.add_task(self._process, pdf_id, file_path)
        logger.info(f"PDF {pdf_id} uploaded, processing queued")
        return {"id": pdf_id, "name": file.filename, "status": "queued"}

    async def _process(self, pdf_id: str, file_path: str):
        from app.core.database import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            try:
                await document_repo.update_status(db, pdf_id, "processing", "Detecting PDF type...")
                await db.commit()

                pdf_type = detect_pdf_type(file_path)

                processed_path = file_path
                ocr_applied = False

                if pdf_type in ("scanned", "handwritten"):
                    await document_repo.update_status(db, pdf_id, "processing", "Running OCR...")
                    await db.commit()
                    processed_path = run_ocr(file_path)
                    ocr_applied = True

                await document_repo.update_status(db, pdf_id, "processing", "Extracting and indexing text...")
                await db.commit()

                chunks = extract_chunks(processed_path)
                if not chunks:
                    raise ValueError("No text could be extracted from this PDF")

                total_pages = get_page_count(processed_path)
                await indexing_service.index_chunks(db, pdf_id, chunks)

                await document_repo.update_fields(db, pdf_id, {
                    "status": "ready",
                    "status_message": f"{len(chunks)} chunks indexed across {total_pages} pages",
                    "pdf_type": pdf_type,
                    "ocr_applied": ocr_applied,
                    "total_pages": total_pages,
                    "file_path": processed_path,
                })
                await db.commit()
                logger.info(f"PDF {pdf_id} ready — {len(chunks)} chunks")

            except Exception as e:
                logger.error(f"Processing failed for PDF {pdf_id}: {e}")
                await document_repo.update_status(db, pdf_id, "failed", str(e))
                await db.commit()

    async def get_status(self, db: AsyncSession, pdf_id: str) -> dict:
        pdf = await document_repo.get_by_id(db, pdf_id)
        if not pdf:
            raise PDFNotFoundError(pdf_id)
        return {
            "id": pdf.id,
            "name": pdf.name,
            "status": pdf.status,
            "progress": STATUS_PROGRESS.get(pdf.status, 0),
            "message": pdf.status_message,
            "pdf_type": pdf.pdf_type,
            "total_pages": pdf.total_pages,
        }

    async def get_meta(self, db: AsyncSession, pdf_id: str):
        pdf = await document_repo.get_by_id(db, pdf_id)
        if not pdf:
            raise PDFNotFoundError(pdf_id)
        return pdf

    async def get_file_path(self, db: AsyncSession, pdf_id: str) -> str:
        pdf = await document_repo.get_by_id(db, pdf_id)
        if not pdf:
            raise PDFNotFoundError(pdf_id)
        return pdf.file_path

    async def list_by_user(self, db: AsyncSession, user_id: str) -> dict:
        pdfs = await document_repo.get_all_by_user(db, user_id)
        return {"pdfs": pdfs, "total": len(pdfs)}

    async def delete(self, db: AsyncSession, pdf_id: str):
        pdf = await document_repo.get_by_id(db, pdf_id)
        if not pdf:
            raise PDFNotFoundError(pdf_id)

        for path in [pdf.file_path, pdf.file_path.replace(".pdf", "_ocr.pdf")]:
            try:
                if path and os.path.exists(path):
                    os.remove(path)
            except Exception as e:
                logger.warning(f"Could not remove file {path}: {e}")

        indexing_service.delete_index(pdf_id)
        await document_repo.delete(db, pdf_id)
        await db.commit()

    def _validate_file(self, file: UploadFile):
        if not file.filename or not file.filename.lower().endswith(".pdf"):
            raise InvalidFileTypeError()


document_service = DocumentService()
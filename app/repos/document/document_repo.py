from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.models.pdf import PDF


class DocumentRepo:

    async def create(self, db: AsyncSession, data: dict) -> PDF:
        pdf = PDF(**data)
        db.add(pdf)
        await db.flush()
        await db.refresh(pdf)
        return pdf

    async def get_by_id(self, db: AsyncSession, pdf_id: str) -> PDF | None:
        result = await db.execute(select(PDF).where(PDF.id == pdf_id))
        return result.scalar_one_or_none()

    async def get_all_by_user(self, db: AsyncSession, user_id: str) -> list[PDF]:
        result = await db.execute(
            select(PDF)
            .where(PDF.user_id == user_id)
            .order_by(PDF.created_at.desc())
        )
        return list(result.scalars().all())

    async def update_status(
        self,
        db: AsyncSession,
        pdf_id: str,
        status: str,
        message: str | None = None,
    ) -> PDF | None:
        pdf = await self.get_by_id(db, pdf_id)
        if pdf:
            pdf.status = status
            if message is not None:
                pdf.status_message = message
            await db.flush()
        return pdf

    async def update_fields(self, db: AsyncSession, pdf_id: str, data: dict) -> PDF | None:
        pdf = await self.get_by_id(db, pdf_id)
        if pdf:
            for key, value in data.items():
                setattr(pdf, key, value)
            await db.flush()
        return pdf

    async def delete(self, db: AsyncSession, pdf_id: str) -> bool:
        result = await db.execute(delete(PDF).where(PDF.id == pdf_id))
        return result.rowcount > 0


document_repo = DocumentRepo()
"""Language-related endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Language

router = APIRouter(prefix="/api/languages", tags=["languages"])


@router.get("")
async def get_languages(db: AsyncSession = Depends(get_db)):
    """Get all available languages."""
    result = await db.execute(select(Language).order_by(Language.name))
    languages = result.scalars().all()
    return [{"code": lang.code, "name": lang.name} for lang in languages]

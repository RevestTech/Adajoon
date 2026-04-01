from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import HealthCheckResult
from app.services.healthcheck_service import check_channel, check_channels_batch

router = APIRouter(prefix="/api/healthcheck", tags=["healthcheck"])


@router.post("/{channel_id}", response_model=HealthCheckResult)
async def healthcheck_channel(channel_id: str, db: AsyncSession = Depends(get_db)):
    result = await check_channel(db, channel_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.post("/batch", response_model=list[HealthCheckResult])
async def healthcheck_batch(
    channel_ids: list[str] = Body(..., max_length=50),
    db: AsyncSession = Depends(get_db),
):
    if len(channel_ids) > 50:
        raise HTTPException(status_code=400, detail="Maximum 50 channels per batch")
    results = await check_channels_batch(db, channel_ids)
    return [r for r in results if "error" not in r]

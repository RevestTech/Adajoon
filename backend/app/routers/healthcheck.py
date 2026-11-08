from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import HealthCheckResult, ValidatorStatusBuckets, ValidatorStatusOut
from app.services.healthcheck_service import check_channel, check_channels_batch
from app.services.validator_service import get_validator_status

router = APIRouter(prefix="/api/healthcheck", tags=["healthcheck"])

validator_router = APIRouter(prefix="/api/validator", tags=["validator"])


@router.post("/{channel_id}", response_model=HealthCheckResult)
async def healthcheck_channel(channel_id: str, db: AsyncSession = Depends(get_db)):
    try:
        result = await check_channel(db, channel_id)
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        # Log the error for debugging
        import logging

        logging.getLogger(__name__).error(
            f"Healthcheck failed for channel {channel_id}: {e}"
        )
        raise HTTPException(status_code=500, detail="Healthcheck failed")


@router.post("/batch", response_model=list[HealthCheckResult])
async def healthcheck_batch(
    channel_ids: list[str] = Body(..., max_length=50),
    db: AsyncSession = Depends(get_db),
):
    if len(channel_ids) > 50:
        raise HTTPException(status_code=400, detail="Maximum 50 channels per batch")
    results = await check_channels_batch(db, channel_ids)
    return [r for r in results if "error" not in r]


@validator_router.get("/status", response_model=ValidatorStatusOut)
async def validator_status(db: AsyncSession = Depends(get_db)):
    data = await get_validator_status(db)
    return ValidatorStatusOut(
        channels=ValidatorStatusBuckets(**data["channels"]),
        radio=ValidatorStatusBuckets(**data["radio"]),
        last_validation_cycle_at=data["last_validation_cycle_at"],
    )

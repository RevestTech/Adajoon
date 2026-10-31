from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AppSetting

_TRUE_VALUES = {"true", "1", "yes"}


async def get_setting(
    db: AsyncSession, key: str, default: str | None = None
) -> str | None:
    result = await db.execute(select(AppSetting.value).where(AppSetting.key == key))
    value = result.scalar_one_or_none()
    return value if value is not None else default


async def set_setting(db: AsyncSession, key: str, value: str) -> None:
    stmt = pg_insert(AppSetting).values(key=key, value=value)
    stmt = stmt.on_conflict_do_update(
        index_elements=[AppSetting.key],
        set_={"value": stmt.excluded.value, "updated_at": stmt.excluded.updated_at},
    )
    await db.execute(stmt)
    await db.commit()


async def get_bool_setting(db: AsyncSession, key: str, default: bool) -> bool:
    value = await get_setting(db, key)
    if value is None:
        return default
    return value.strip().lower() in _TRUE_VALUES


async def set_bool_setting(db: AsyncSession, key: str, value: bool) -> None:
    await set_setting(db, key, "true" if value else "false")

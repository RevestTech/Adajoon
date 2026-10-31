from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Movie


async def list_movies(db: AsyncSession, *, active_only: bool = False) -> list[Movie]:
    stmt = select(Movie)
    if active_only:
        stmt = stmt.where(Movie.is_active.is_(True))
    stmt = stmt.order_by(Movie.sort_order, Movie.title)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_movie(db: AsyncSession, movie_id: int) -> Movie | None:
    result = await db.execute(select(Movie).where(Movie.id == movie_id))
    return result.scalar_one_or_none()


async def create_movie(db: AsyncSession, data: dict) -> Movie:
    movie = Movie(**data)
    db.add(movie)
    await db.commit()
    await db.refresh(movie)
    return movie


_CLEARABLE_FIELDS = {"year", "duration_minutes"}


async def update_movie(db: AsyncSession, movie: Movie, data: dict) -> Movie:
    for field, value in data.items():
        if value is None and field not in _CLEARABLE_FIELDS:
            continue
        setattr(movie, field, value)
    await db.commit()
    await db.refresh(movie)
    return movie


async def delete_movie(db: AsyncSession, movie: Movie) -> None:
    await db.delete(movie)
    await db.commit()

"""Public movie catalog - syndicated titles, Adajoon hosts no video itself."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import MovieOut
from app.services import movie_service

router = APIRouter(prefix="/api/movies", tags=["movies"])


@router.get("", response_model=list[MovieOut])
async def list_movies(db: AsyncSession = Depends(get_db)):
    return await movie_service.list_movies(db, active_only=True)


@router.get("/{movie_id}", response_model=MovieOut)
async def get_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await movie_service.get_movie(db, movie_id)
    if not movie or not movie.is_active:
        raise HTTPException(status_code=404, detail="Movie not found")
    return movie

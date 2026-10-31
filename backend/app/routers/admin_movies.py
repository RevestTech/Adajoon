"""Admin-only CRUD for the syndicated movie catalog.

Adajoon hosts no video for movies - stream_url points at a syndication
partner's (or other licensed source's) already-hosted stream, the same
model as Channel.stream_url. Until an automated feed partner is wired
up, titles are added here by hand.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.csrf import verify_csrf_token
from app.database import get_db
from app.middleware.admin_required import require_admin
from app.models import User
from app.schemas import MovieCreate, MovieOut, MovieUpdate
from app.services import movie_service, tmdb_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin/movies", tags=["admin", "movies"])


@router.get("/tmdb-search")
async def admin_tmdb_search(
    q: str = Query(..., min_length=1),
    admin_user: User = Depends(require_admin),
):
    """Look up poster art/metadata candidates from TMDb for the add-movie
    form. Never used at playback time - purely an admin convenience."""
    try:
        return await tmdb_service.search_movies(q)
    except tmdb_service.TmdbNotConfigured:
        raise HTTPException(
            status_code=503,
            detail="TMDB_API_KEY is not configured - get a free key at "
            "https://www.themoviedb.org/settings/api",
        )
    except Exception:
        logger.exception("TMDb search failed for query %r", q)
        raise HTTPException(status_code=502, detail="TMDb lookup failed")


@router.get("", response_model=list[MovieOut])
async def admin_list_movies(
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return await movie_service.list_movies(db)


@router.post("", response_model=MovieOut)
async def admin_create_movie(
    payload: MovieCreate,
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    _csrf: None = Depends(verify_csrf_token),
):
    movie = await movie_service.create_movie(db, payload.model_dump())
    logger.info("Admin %s added movie %s", admin_user.email, movie.title)
    return movie


@router.patch("/{movie_id}", response_model=MovieOut)
async def admin_update_movie(
    movie_id: int,
    payload: MovieUpdate,
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    _csrf: None = Depends(verify_csrf_token),
):
    movie = await movie_service.get_movie(db, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    movie = await movie_service.update_movie(
        db, movie, payload.model_dump(exclude_unset=True)
    )
    logger.info("Admin %s updated movie %s", admin_user.email, movie.title)
    return movie


@router.delete("/{movie_id}")
async def admin_delete_movie(
    movie_id: int,
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    _csrf: None = Depends(verify_csrf_token),
):
    movie = await movie_service.get_movie(db, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    await movie_service.delete_movie(db, movie)
    logger.info("Admin %s deleted movie %s", admin_user.email, movie.title)
    return {"success": True}

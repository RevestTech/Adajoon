"""Playlist endpoints."""
import json
from typing import Literal, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_db
from app.models import Playlist, PlaylistItem, User
from app.routers.auth import require_user
from app.csrf import verify_csrf_token

router = APIRouter(prefix="/api/playlists", tags=["playlists"])


# ---------------------------------------------------------------------------
# Request/Response Models
# ---------------------------------------------------------------------------

class CreatePlaylistRequest(BaseModel):
    name: str
    description: Optional[str] = ""
    is_public: bool = False


class UpdatePlaylistRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_public: Optional[bool] = None


class AddItemRequest(BaseModel):
    item_type: Literal["tv", "radio"]
    item_id: str
    item_data: str  # JSON string with name, logo, etc.


class ReorderRequest(BaseModel):
    item_ids: list[int]  # New order of playlist item IDs


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/")
async def get_playlists(
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all playlists for current user."""
    result = await db.execute(
        select(Playlist)
        .where(Playlist.user_id == user.id)
        .order_by(Playlist.created_at.desc())
    )
    playlists = result.scalars().all()
    
    return [
        {
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "is_public": p.is_public,
            "item_count": len(p.items) if p.items else 0,
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "updated_at": p.updated_at.isoformat() if p.updated_at else None,
        }
        for p in playlists
    ]


@router.post("/")
async def create_playlist(
    request: CreatePlaylistRequest,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
    _csrf: None = Depends(verify_csrf_token),
):
    """Create a new playlist."""
    playlist = Playlist(
        user_id=user.id,
        name=request.name,
        description=request.description or "",
        is_public=request.is_public,
    )
    db.add(playlist)
    await db.commit()
    await db.refresh(playlist)
    
    return {
        "id": playlist.id,
        "name": playlist.name,
        "description": playlist.description,
        "is_public": playlist.is_public,
        "item_count": 0,
        "created_at": playlist.created_at.isoformat(),
    }


@router.get("/{playlist_id}")
async def get_playlist(
    playlist_id: int,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    """Get playlist details with items."""
    result = await db.execute(
        select(Playlist)
        .where(Playlist.id == playlist_id)
    )
    playlist = result.scalar_one_or_none()
    
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    # Check ownership or public access
    if playlist.user_id != user.id and not playlist.is_public:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get items
    items_result = await db.execute(
        select(PlaylistItem)
        .where(PlaylistItem.playlist_id == playlist_id)
        .order_by(PlaylistItem.position)
    )
    items = items_result.scalars().all()
    
    return {
        "id": playlist.id,
        "name": playlist.name,
        "description": playlist.description,
        "is_public": playlist.is_public,
        "created_at": playlist.created_at.isoformat(),
        "updated_at": playlist.updated_at.isoformat(),
        "items": [
            {
                "id": item.id,
                "item_type": item.item_type,
                "item_id": item.item_id,
                "item_data": json.loads(item.item_data or "{}"),
                "position": item.position,
                "added_at": item.added_at.isoformat() if item.added_at else None,
            }
            for item in items
        ],
    }


@router.put("/{playlist_id}")
async def update_playlist(
    playlist_id: int,
    request: UpdatePlaylistRequest,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
    _csrf: None = Depends(verify_csrf_token),
):
    """Update playlist metadata."""
    result = await db.execute(
        select(Playlist)
        .where(Playlist.id == playlist_id, Playlist.user_id == user.id)
    )
    playlist = result.scalar_one_or_none()
    
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    if request.name is not None:
        playlist.name = request.name
    if request.description is not None:
        playlist.description = request.description
    if request.is_public is not None:
        playlist.is_public = request.is_public
    
    await db.commit()
    await db.refresh(playlist)
    
    return {
        "id": playlist.id,
        "name": playlist.name,
        "description": playlist.description,
        "is_public": playlist.is_public,
    }


@router.delete("/{playlist_id}")
async def delete_playlist(
    playlist_id: int,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
    _csrf: None = Depends(verify_csrf_token),
):
    """Delete a playlist."""
    result = await db.execute(
        select(Playlist)
        .where(Playlist.id == playlist_id, Playlist.user_id == user.id)
    )
    playlist = result.scalar_one_or_none()
    
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    await db.delete(playlist)
    await db.commit()
    
    return {"status": "deleted"}


@router.post("/{playlist_id}/items")
async def add_playlist_item(
    playlist_id: int,
    request: AddItemRequest,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
    _csrf: None = Depends(verify_csrf_token),
):
    """Add an item to playlist."""
    # Verify ownership
    result = await db.execute(
        select(Playlist)
        .where(Playlist.id == playlist_id, Playlist.user_id == user.id)
    )
    playlist = result.scalar_one_or_none()
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    # Get current max position
    max_pos_result = await db.execute(
        select(func.coalesce(func.max(PlaylistItem.position), -1))
        .where(PlaylistItem.playlist_id == playlist_id)
    )
    max_position = max_pos_result.scalar()
    
    # Add item
    item = PlaylistItem(
        playlist_id=playlist_id,
        item_type=request.item_type,
        item_id=request.item_id,
        item_data=request.item_data,
        position=max_position + 1,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    
    return {
        "id": item.id,
        "item_type": item.item_type,
        "item_id": item.item_id,
        "position": item.position,
    }


@router.delete("/{playlist_id}/items/{item_id}")
async def remove_playlist_item(
    playlist_id: int,
    item_id: int,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
    _csrf: None = Depends(verify_csrf_token),
):
    """Remove an item from playlist."""
    # Verify ownership
    result = await db.execute(
        select(Playlist)
        .where(Playlist.id == playlist_id, Playlist.user_id == user.id)
    )
    playlist = result.scalar_one_or_none()
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    # Delete item
    await db.execute(
        delete(PlaylistItem)
        .where(PlaylistItem.id == item_id, PlaylistItem.playlist_id == playlist_id)
    )
    await db.commit()
    
    return {"status": "removed"}


@router.post("/{playlist_id}/reorder")
async def reorder_playlist(
    playlist_id: int,
    request: ReorderRequest,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
    _csrf: None = Depends(verify_csrf_token),
):
    """Reorder playlist items."""
    # Verify ownership
    result = await db.execute(
        select(Playlist)
        .where(Playlist.id == playlist_id, Playlist.user_id == user.id)
    )
    playlist = result.scalar_one_or_none()
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    # Update positions
    for position, item_id in enumerate(request.item_ids):
        await db.execute(
            PlaylistItem.__table__.update()
            .where(PlaylistItem.id == item_id, PlaylistItem.playlist_id == playlist_id)
            .values(position=position)
        )
    
    await db.commit()
    return {"status": "reordered"}

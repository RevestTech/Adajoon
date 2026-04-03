from sqlalchemy import Column, String, Text, Boolean, Integer, ForeignKey, Index, DateTime, func
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(320), unique=True, nullable=False, index=True)
    name = Column(String(255), default="")
    picture = Column(Text, default="")
    provider = Column(String(50), default="google")
    provider_id = Column(String(255), default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Parental controls
    kids_mode_enabled = Column(Boolean, default=False)
    parental_pin_hash = Column(String(255), default="")
    
    # Subscription
    stripe_customer_id = Column(String(255), default="", index=True)
    subscription_tier = Column(String(50), default="free", index=True)  # free, plus, pro, family
    subscription_status = Column(String(50), default="")  # active, canceled, past_due, etc.
    subscription_ends_at = Column(DateTime(timezone=True), default=None)

    favorites = relationship("UserFavorite", back_populates="user", cascade="all, delete-orphan")


class UserFavorite(Base):
    __tablename__ = "user_favorites"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    item_type = Column(String(10), nullable=False)
    item_id = Column(String(255), nullable=False)
    item_data = Column(Text, default="{}")
    added_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="favorites")

    __table_args__ = (
        Index("ix_user_fav_unique", "user_id", "item_type", "item_id", unique=True),
    )


class UserVote(Base):
    __tablename__ = "user_votes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    item_type = Column(String(10), nullable=False)
    item_id = Column(String(255), nullable=False)
    vote_type = Column(String(20), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")

    __table_args__ = (
        Index("ix_user_vote_unique", "user_id", "item_type", "item_id", "vote_type", unique=True),
        Index("ix_vote_item", "item_type", "item_id"),
    )


class WatchHistory(Base):
    __tablename__ = "watch_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    item_type = Column(String(10), nullable=False)
    item_id = Column(String(255), nullable=False)
    item_name = Column(String(512), nullable=False)
    item_logo = Column(Text, default="")
    watched_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    duration_seconds = Column(Integer, default=0)

    user = relationship("User")

    __table_args__ = (
        Index("ix_watch_history_user_type", "user_id", "item_type", "watched_at"),
        Index("ix_watch_history_item", "item_type", "item_id"),
    )


class Playlist(Base):
    __tablename__ = "playlists"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, default="")
    is_public = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User")
    items = relationship("PlaylistItem", back_populates="playlist", cascade="all, delete-orphan")


class PlaylistItem(Base):
    __tablename__ = "playlist_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    playlist_id = Column(Integer, ForeignKey("playlists.id", ondelete="CASCADE"), nullable=False, index=True)
    item_type = Column(String(10), nullable=False)  # 'tv' or 'radio'
    item_id = Column(String(255), nullable=False)
    item_data = Column(Text, default="{}")  # JSON: {name, logo, country, etc.}
    position = Column(Integer, default=0)
    added_at = Column(DateTime(timezone=True), server_default=func.now())

    playlist = relationship("Playlist", back_populates="items")

    __table_args__ = (
        Index("ix_playlist_items_playlist_position", "playlist_id", "position"),
        Index("ix_playlist_items_item", "item_type", "item_id"),
    )


class Passkey(Base):
    __tablename__ = "passkeys"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    credential_id = Column(Text, nullable=False, unique=True)
    public_key = Column(Text, nullable=False)
    sign_count = Column(Integer, default=0)
    transports = Column(Text, default="[]")
    name = Column(String(255), default="Passkey")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", backref="passkeys")


class Category(Base):
    __tablename__ = "categories"

    id = Column(String, primary_key=True)
    name = Column(String(255), nullable=False, unique=True)

    channels = relationship("Channel", back_populates="category")


class Language(Base):
    __tablename__ = "languages"

    code = Column(String(10), primary_key=True)
    name = Column(String(255), nullable=False)


class Country(Base):
    __tablename__ = "countries"

    code = Column(String(10), primary_key=True)
    name = Column(String(255), nullable=False)
    flag = Column(String(10), default="")


class Channel(Base):
    __tablename__ = "channels"

    id = Column(String, primary_key=True)
    name = Column(String(500), nullable=False, index=True)
    alt_names = Column(Text, default="")
    network = Column(String(500), default="")
    country_code = Column(String(10), ForeignKey("countries.code"), default="", index=True)
    subdivision = Column(String(100), default="")
    city = Column(String(255), default="")
    categories = Column(String(500), default="")
    category_id = Column(String, ForeignKey("categories.id"), nullable=True, index=True)
    is_nsfw = Column(Boolean, default=False)
    launched = Column(String(50), default="")
    closed = Column(String(50), default="")
    website = Column(Text, default="")
    logo = Column(Text, default="")
    stream_url = Column(Text, default="")
    languages = Column(Text, default="")
    is_active = Column(Boolean, default=True)
    updated_at = Column(String(50), default="")
    health_status = Column(String(20), default="unknown")
    health_checked_at = Column(String(50), default="")
    last_validated_at = Column(String(50), default="")

    category = relationship("Category", back_populates="channels")

    __table_args__ = (
        Index("ix_channels_name_trgm", "name"),
        Index("ix_channels_health_status", "health_status"),
        Index("ix_channels_health_checked_at", "health_checked_at"),
    )


class RadioStation(Base):
    __tablename__ = "radio_stations"

    id = Column(String, primary_key=True)
    name = Column(String(500), nullable=False, index=True)
    url = Column(Text, default="")
    url_resolved = Column(Text, default="")
    homepage = Column(Text, default="")
    favicon = Column(Text, default="")
    tags = Column(Text, default="")
    country = Column(String(255), default="")
    country_code = Column(String(10), default="", index=True)
    state = Column(String(255), default="")
    language = Column(String(500), default="")
    codec = Column(String(50), default="")
    bitrate = Column(Integer, default=0)
    votes = Column(Integer, default=0)
    last_check_ok = Column(Boolean, default=False)
    health_status = Column(String(20), default="unknown")
    health_checked_at = Column(String(50), default="")
    geo_lat = Column(String(50), default="")
    geo_long = Column(String(50), default="")

    __table_args__ = (
        Index("ix_radio_name", "name"),
        Index("ix_radio_country", "country_code"),
        Index("ix_radio_health_status", "health_status"),
        Index("ix_radio_last_check_ok", "last_check_ok"),
        Index("ix_radio_votes_desc", votes.desc()),
        Index("ix_radio_health_checked_at", "health_checked_at"),
    )


class Stream(Base):
    __tablename__ = "streams"

    id = Column(Integer, primary_key=True, autoincrement=True)
    channel_id = Column(String, ForeignKey("channels.id"), index=True)
    url = Column(Text, nullable=False)
    http_referrer = Column(Text, default="")
    user_agent = Column(Text, default="")
    status = Column(String(50), default="unknown")
    added_at = Column(String(50), default="")

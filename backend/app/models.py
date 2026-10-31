from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
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
    last_login_at = Column(DateTime(timezone=True), default=None)

    # Roles and permissions
    is_admin = Column(Boolean, default=False, index=True)
    role = Column(String(50), default="user", index=True)  # user, moderator, admin

    # Parental controls
    kids_mode_enabled = Column(Boolean, default=False)
    parental_pin_hash = Column(String(255), default="")

    # Subscription
    stripe_customer_id = Column(String(255), default="", index=True)
    subscription_tier = Column(
        String(50), default="free", index=True
    )  # free, plus, pro, family
    subscription_status = Column(
        String(50), default=""
    )  # active, canceled, past_due, etc.
    subscription_ends_at = Column(DateTime(timezone=True), default=None)

    favorites = relationship(
        "UserFavorite", back_populates="user", cascade="all, delete-orphan"
    )


class UserFavorite(Base):
    __tablename__ = "user_favorites"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
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
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    item_type = Column(String(10), nullable=False)
    item_id = Column(String(255), nullable=False)
    vote_type = Column(String(20), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")

    __table_args__ = (
        Index(
            "ix_user_vote_unique",
            "user_id",
            "item_type",
            "item_id",
            "vote_type",
            unique=True,
        ),
        Index("ix_vote_item", "item_type", "item_id"),
    )


class WatchHistory(Base):
    __tablename__ = "watch_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
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
        # Named to match the on_conflict_do_update() constraint in
        # history.py's record_watch_history - one row per item per user.
        # Must be a real constraint (not just a unique index): Postgres's
        # ON CONFLICT ON CONSTRAINT looks it up in pg_constraint, which a
        # plain CREATE UNIQUE INDEX never registers.
        UniqueConstraint(
            "user_id", "item_type", "item_id", name="ix_watch_history_user_item_recent"
        ),
    )


class Playlist(Base):
    __tablename__ = "playlists"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name = Column(String(255), nullable=False)
    description = Column(Text, default="")
    is_public = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user = relationship("User")
    items = relationship(
        "PlaylistItem", back_populates="playlist", cascade="all, delete-orphan"
    )


class PlaylistItem(Base):
    __tablename__ = "playlist_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    playlist_id = Column(
        Integer,
        ForeignKey("playlists.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
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
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
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
    country_code = Column(
        String(10), ForeignKey("countries.code"), default="", index=True
    )
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
    updated_at = Column(DateTime(timezone=True), nullable=True)
    health_status = Column(String(20), default="unknown")
    health_checked_at = Column(DateTime(timezone=True), nullable=True)
    last_validated_at = Column(DateTime(timezone=True), nullable=True)
    # Admin override, independent of is_active (which the IPTV catalog sync
    # overwrites every run). A hidden channel stays hidden across syncs.
    admin_hidden = Column(Boolean, server_default="false", index=True)

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
    health_checked_at = Column(DateTime(timezone=True), nullable=True)
    geo_lat = Column(String(50), default="")
    geo_long = Column(String(50), default="")
    # Admin override, independent of last_check_ok (which the sync job
    # overwrites). A hidden station stays hidden across syncs.
    admin_hidden = Column(Boolean, server_default="false", index=True)

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
    added_at = Column(DateTime(timezone=True), nullable=True)


class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    session_id = Column(String(255), nullable=False, index=True)
    event_name = Column(String(100), nullable=False, index=True)
    properties = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    user = relationship("User")

    __table_args__ = (
        Index("ix_analytics_event_name_created", "event_name", "created_at"),
        Index("ix_analytics_user_created", "user_id", "created_at"),
        Index("ix_analytics_session_created", "session_id", "created_at"),
    )


class EpgProgramme(Base):
    """XMLTV programme row; channel_id matches iptv-org Channel.id (Slug.cc) when available.

    No FK to channels: guide packs include ids/feeds not present in our channel table.
    """

    __tablename__ = "epg_programmes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    channel_id = Column(String, nullable=False, index=True)
    start_at = Column(DateTime(timezone=True), nullable=False)
    stop_at = Column(DateTime(timezone=True), nullable=False)
    title = Column(String(500), nullable=False, default="")
    subtitle = Column(String(500), default="")
    description = Column(Text, default="")
    category = Column(String(255), default="")

    __table_args__ = (
        UniqueConstraint("channel_id", "start_at", name="uq_epg_channel_start"),
        Index("ix_epg_programmes_channel_start", "channel_id", "start_at"),
        Index("ix_epg_programmes_start_stop", "start_at", "stop_at"),
    )


class PricingTier(Base):
    """A subscription tier, editable by admins instead of hardcoded in the API."""

    __tablename__ = "pricing_tiers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    monthly_price_cents = Column(Integer, nullable=False, server_default="0")
    annual_price_cents = Column(Integer, default=None)
    stripe_price_id_monthly = Column(String(255), server_default="")
    stripe_price_id_annual = Column(String(255), server_default="")
    sort_order = Column(Integer, server_default="0", index=True)
    is_active = Column(Boolean, server_default="true", index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    features = relationship(
        "PricingFeature", back_populates="tier", cascade="all, delete-orphan"
    )


class PricingFeature(Base):
    """A feature line shown on a tier, or sold as a standalone add-on.

    A feature with a null tier_id and a non-zero price is an a-la-carte
    add-on rather than something bundled into a subscription tier.
    """

    __tablename__ = "pricing_features"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tier_id = Column(
        Integer,
        ForeignKey("pricing_tiers.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    key = Column(String(100), nullable=False, index=True)
    label = Column(String(255), nullable=False)
    is_addon = Column(Boolean, server_default="false")
    addon_price_cents = Column(Integer, server_default="0")
    sort_order = Column(Integer, server_default="0")
    is_active = Column(Boolean, server_default="true")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    tier = relationship("PricingTier", back_populates="features")

    __table_args__ = (
        UniqueConstraint("tier_id", "key", name="uq_pricing_feature_tier_key"),
    )


class PricingDiscount(Base):
    """An admin-managed promo code, optionally restricted to one tier."""

    __tablename__ = "pricing_discounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    label = Column(String(255), server_default="")
    percent_off = Column(Integer, default=None)
    amount_off_cents = Column(Integer, default=None)
    tier_id = Column(
        Integer,
        ForeignKey("pricing_tiers.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    stripe_coupon_id = Column(String(255), server_default="")
    starts_at = Column(DateTime(timezone=True), default=None)
    ends_at = Column(DateTime(timezone=True), default=None)
    max_redemptions = Column(Integer, default=None)
    redemption_count = Column(Integer, server_default="0")
    is_active = Column(Boolean, server_default="true", index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    tier = relationship("PricingTier")


class Movie(Base):
    """A syndicated title: Adajoon hosts no video itself, `stream_url` points
    at a syndication partner's (or other licensed source's) already-hosted,
    already-playable stream - the same model as Channel.stream_url."""

    __tablename__ = "movies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False, index=True)
    synopsis = Column(Text, server_default="")
    poster_url = Column(Text, server_default="")
    year = Column(Integer, nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    genres = Column(String(500), server_default="")
    source = Column(String(255), server_default="")
    stream_url = Column(Text, nullable=False)
    sort_order = Column(Integer, server_default="0")
    is_active = Column(Boolean, server_default="true", index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AppSetting(Base):
    """A small admin-editable key/value store for simple on/off switches
    (e.g. the ads kill switch) - not a generic feature-flag platform, just
    somewhere for toggles to live without a bespoke column/table each."""

    __tablename__ = "app_settings"

    key = Column(String(100), primary_key=True)
    value = Column(Text, nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now())

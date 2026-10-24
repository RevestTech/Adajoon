from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


def _none_to_empty(v: Any) -> Any:
    if v is None:
        return ""
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return str(v)
    return v


def _coerce_timestamp(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, (datetime, date)):
        return v.isoformat()
    if isinstance(v, str):
        return v
    return str(v)


def _none_to_unknown(v: Any) -> Any:
    if v is None:
        return "unknown"
    return v


def _none_bool(default: bool):
    def _inner(v: Any) -> Any:
        if v is None:
            return default
        return v

    return _inner


def _none_int(default: int):
    def _inner(v: Any) -> Any:
        if v is None:
            return default
        return v

    return _inner


class CategoryOut(BaseModel):
    id: str
    name: str
    channel_count: int = 0
    live_count: int = 0
    verified_count: int = 0

    model_config = {"from_attributes": True}


class CountryOut(BaseModel):
    code: str
    name: str
    flag: str = ""
    channel_count: int = 0
    live_count: int = 0
    verified_count: int = 0

    model_config = {"from_attributes": True}


class LanguageOut(BaseModel):
    code: str
    name: str

    model_config = {"from_attributes": True}


class ChannelOut(BaseModel):
    id: str
    name: str
    alt_names: str = ""
    network: str = ""
    country_code: str = ""
    categories: str = ""
    is_nsfw: bool = False
    website: str = ""
    logo: str = ""
    stream_url: str = ""
    languages: str = ""
    is_active: bool = True
    health_status: str = "unknown"
    health_checked_at: str = ""
    last_validated_at: str = ""

    model_config = {"from_attributes": True}

    @field_validator(
        "alt_names",
        "network",
        "country_code",
        "categories",
        "website",
        "logo",
        "stream_url",
        "languages",
        mode="before",
    )
    @classmethod
    def coerce_optional_str(cls, v: Any) -> Any:
        return _none_to_empty(v)

    @field_validator("health_status", mode="before")
    @classmethod
    def coerce_health_status(cls, v: Any) -> Any:
        return _none_to_unknown(v)

    @field_validator("health_checked_at", "last_validated_at", mode="before")
    @classmethod
    def coerce_timestamps(cls, v: Any) -> str:
        return _coerce_timestamp(v)

    @field_validator("is_nsfw", mode="before")
    @classmethod
    def coerce_is_nsfw(cls, v: Any) -> Any:
        return _none_bool(False)(v)

    @field_validator("is_active", mode="before")
    @classmethod
    def coerce_is_active(cls, v: Any) -> Any:
        return _none_bool(True)(v)


class HealthCheckResult(BaseModel):
    channel_id: str
    stream_url: str
    status: str
    response_time_ms: int
    detail: str = ""
    checked_at: str


class StreamOut(BaseModel):
    id: int
    channel_id: str
    url: str
    status: str = "unknown"

    model_config = {"from_attributes": True}


class ChannelSearchParams(BaseModel):
    query: str | None = None
    category: str | None = None
    country: str | None = None
    language: str | None = None
    live_only: bool = False
    status: str | None = None
    page: int = 1
    per_page: int = 40


class PaginatedChannels(BaseModel):
    channels: list[ChannelOut]
    total: int
    page: int
    per_page: int
    total_pages: int


class ForYouResponse(BaseModel):
    channels: list[ChannelOut]
    category: str | None = None


class RadioStationOut(BaseModel):
    id: str
    name: str
    url: str = ""
    url_resolved: str = ""
    homepage: str = ""
    favicon: str = ""
    tags: str = ""
    country: str = ""
    country_code: str = ""
    state: str = ""
    language: str = ""
    codec: str = ""
    bitrate: int = 0
    votes: int = 0
    last_check_ok: bool = False
    health_status: str = "unknown"
    health_checked_at: str = ""
    geo_lat: str = ""
    geo_long: str = ""

    model_config = {"from_attributes": True}

    @field_validator(
        "url",
        "url_resolved",
        "homepage",
        "favicon",
        "tags",
        "country",
        "country_code",
        "state",
        "language",
        "codec",
        "geo_lat",
        "geo_long",
        mode="before",
    )
    @classmethod
    def coerce_optional_str(cls, v: Any) -> Any:
        return _none_to_empty(v)

    @field_validator("health_status", mode="before")
    @classmethod
    def coerce_health_status(cls, v: Any) -> Any:
        return _none_to_unknown(v)

    @field_validator("health_checked_at", mode="before")
    @classmethod
    def coerce_timestamps(cls, v: Any) -> str:
        return _coerce_timestamp(v)

    @field_validator("last_check_ok", mode="before")
    @classmethod
    def coerce_last_check_ok(cls, v: Any) -> Any:
        return _none_bool(False)(v)

    @field_validator("bitrate", "votes", mode="before")
    @classmethod
    def coerce_bitrate_votes(cls, v: Any) -> Any:
        return _none_int(0)(v)


class RadioSearchParams(BaseModel):
    query: str | None = None
    tag: str | None = None
    country: str | None = None
    language: str | None = None
    working_only: bool = False
    status: str | None = None
    page: int = 1
    per_page: int = 40


class PaginatedRadio(BaseModel):
    stations: list[RadioStationOut]
    total: int
    page: int
    per_page: int
    total_pages: int


class RadioTagOut(BaseModel):
    name: str
    station_count: int = 0


class RadioCountryOut(BaseModel):
    country: str
    country_code: str
    station_count: int = 0


class MapStationPin(BaseModel):
    id: str
    name: str
    favicon: str = ""
    geo_lat: float
    geo_long: float
    country_code: str = ""


class MapCluster(BaseModel):
    lat: float
    lng: float
    count: int = Field(..., ge=1)


class MapBboxResponse(BaseModel):
    type: Literal["stations", "clusters"]
    items: list[MapStationPin] | list[MapCluster]
    zoom: int


class StatsOut(BaseModel):
    total_channels: int
    total_categories: int
    total_countries: int
    total_streams: int
    total_radio_stations: int = 0


class ValidatorStatusBuckets(BaseModel):
    total: int
    verified: int
    offline: int
    unknown: int


class ValidatorStatusOut(BaseModel):
    channels: ValidatorStatusBuckets
    radio: ValidatorStatusBuckets
    last_validation_cycle_at: str = ""


class EpgProgrammeOut(BaseModel):
    id: int
    channel_id: str
    start_at: datetime
    stop_at: datetime
    title: str = ""
    subtitle: str = ""
    description: str = ""
    category: str = ""

    model_config = {"from_attributes": True}


class EpgScheduleResponse(BaseModel):
    channel_id: str
    from_at: datetime
    to_at: datetime
    programmes: list[EpgProgrammeOut]


class EpgNowResponse(BaseModel):
    channel_id: str
    now: EpgProgrammeOut | None = None
    next: EpgProgrammeOut | None = None


class EpgOnNowItem(BaseModel):
    channel_id: str
    programme: EpgProgrammeOut


class EpgOnNowResponse(BaseModel):
    items: list[EpgOnNowItem]
    q: str | None = None
    category: str | None = None


class EpgNowBatchResponse(BaseModel):
    """Current programme per channel, for a grid of tiles - only channels
    with something airing now are included."""

    items: dict[str, EpgProgrammeOut]


class EpgScheduleBatchResponse(BaseModel):
    """Full channel x time schedule for a page of channels - the EPG grid
    view. Channels with nothing airing in the window are omitted."""

    from_at: datetime
    to_at: datetime
    items: dict[str, list[EpgProgrammeOut]]


class PricingFeatureOut(BaseModel):
    id: int
    tier_id: int | None
    key: str
    label: str
    is_addon: bool
    addon_price_cents: int
    sort_order: int
    is_active: bool

    model_config = {"from_attributes": True}


class PricingFeatureCreate(BaseModel):
    tier_id: int | None = None
    key: str
    label: str
    is_addon: bool = False
    addon_price_cents: int = 0
    sort_order: int = 0


class PricingFeatureUpdate(BaseModel):
    label: str | None = None
    is_addon: bool | None = None
    addon_price_cents: int | None = None
    sort_order: int | None = None
    is_active: bool | None = None


class PricingTierOut(BaseModel):
    id: int
    key: str
    name: str
    monthly_price_cents: int
    annual_price_cents: int | None
    stripe_price_id_monthly: str
    stripe_price_id_annual: str
    sort_order: int
    is_active: bool
    features: list[PricingFeatureOut] = []

    model_config = {"from_attributes": True}


class PricingTierCreate(BaseModel):
    key: str
    name: str
    monthly_price_cents: int = 0
    annual_price_cents: int | None = None
    stripe_price_id_monthly: str = ""
    stripe_price_id_annual: str = ""
    sort_order: int = 0


class PricingTierUpdate(BaseModel):
    name: str | None = None
    monthly_price_cents: int | None = None
    annual_price_cents: int | None = None
    stripe_price_id_monthly: str | None = None
    stripe_price_id_annual: str | None = None
    sort_order: int | None = None
    is_active: bool | None = None


class PricingDiscountOut(BaseModel):
    id: int
    code: str
    label: str
    percent_off: int | None
    amount_off_cents: int | None
    tier_id: int | None
    starts_at: datetime | None
    ends_at: datetime | None
    max_redemptions: int | None
    redemption_count: int
    is_active: bool

    model_config = {"from_attributes": True}


class PricingDiscountCreate(BaseModel):
    code: str
    label: str = ""
    percent_off: int | None = None
    amount_off_cents: int | None = None
    tier_id: int | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    max_redemptions: int | None = None

    @field_validator("percent_off")
    @classmethod
    def _validate_percent(cls, v: int | None) -> int | None:
        if v is not None and not (0 < v <= 100):
            raise ValueError("percent_off must be between 1 and 100")
        return v


class PricingDiscountUpdate(BaseModel):
    label: str | None = None
    percent_off: int | None = None
    amount_off_cents: int | None = None
    tier_id: int | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    max_redemptions: int | None = None
    is_active: bool | None = None

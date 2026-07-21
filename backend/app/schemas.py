from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, field_validator


def _none_to_empty(v: Any) -> Any:
    if v is None:
        return ""
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

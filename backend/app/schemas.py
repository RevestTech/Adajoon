from pydantic import BaseModel
from typing import Optional


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
    query: Optional[str] = None
    category: Optional[str] = None
    country: Optional[str] = None
    language: Optional[str] = None
    live_only: bool = False
    status: Optional[str] = None
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


class RadioSearchParams(BaseModel):
    query: Optional[str] = None
    tag: Optional[str] = None
    country: Optional[str] = None
    language: Optional[str] = None
    working_only: bool = False
    status: Optional[str] = None
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

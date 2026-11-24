"""API contract between backend and the Android app.

Field names here are the contract. Tell the architect and frontend before changing any of them.
"""

from datetime import datetime, time
from enum import Enum
from typing import Annotated, Literal

from fastapi import Query
from pydantic import AfterValidator, BaseModel, Field

from app.core.clock import to_taipei

# Every datetime in and out of the API goes through this type, so output is always +08:00.
TaipeiDatetime = Annotated[datetime, AfterValidator(to_taipei)]
Lat = Annotated[float, Field(ge=-90, le=90)]
Lon = Annotated[float, Field(ge=-180, le=180)]

# Same rules for query-string parameters.
LatQuery = Annotated[float, Query(ge=-90, le=90)]
LonQuery = Annotated[float, Query(ge=-180, le=180)]
AtQuery = Annotated[datetime | None, Query(description="ISO 8601; no offset = Taipei time; default now")]


class GeocodeLevel(str, Enum):
    exact = "exact"
    approx_suffix = "approx_suffix"
    approx_base_number = "approx_base_number"
    approx_nearby_number = "approx_nearby_number"


class WasteKind(str, Enum):
    general = "general"
    recycle = "recycle"


class EtaStatus(str, Enum):
    live = "live"
    historical = "historical"  # no usable GPS; past arrivals at this stop
    schedule_only = "schedule_only"
    stale = "stale"
    passed = "passed"
    no_data = "no_data"


Risk = Literal["gps_stale", "historical_only", "schedule_only", "approx_location", "walk_fallback"]
WalkMethod = Literal["valhalla", "fallback"]


class ScheduleSlot(BaseModel):
    kind: WasteKind
    start: time
    end: time


class StopBase(BaseModel):
    id: int
    area: str
    village: str
    address: str
    lat: Lat
    lon: Lon
    geocode_level: GeocodeLevel


class StopCandidate(StopBase):
    today_slots: list[ScheduleSlot]
    distance_m: int


class WeeklySlot(BaseModel):
    weekday: int = Field(ge=1, le=7, description="ISO weekday: 1 = Monday ... 7 = Sunday")
    kind: WasteKind
    start: time
    end: time


class StopDetail(StopBase):
    car_licence: str
    weekly: list[WeeklySlot]


class EtaEstimate(BaseModel):
    status: EtaStatus
    eta: TaipeiDatetime | None = None
    eta_low: TaipeiDatetime | None = None
    eta_high: TaipeiDatetime | None = None
    data_time: TaipeiDatetime | None = None
    scheduled_start: TaipeiDatetime | None = None
    scheduled_end: TaipeiDatetime | None = None
    method: str | None = None


class WalkEstimate(BaseModel):
    duration_s: int
    distance_m: int
    method: WalkMethod


class RecommendationRequest(BaseModel):
    lat: Lat
    lon: Lon
    at: TaipeiDatetime | None = None
    deadline: TaipeiDatetime | None = None
    radius_m: int = Field(default=500, ge=100, le=2000)


class RecommendationItem(BaseModel):
    stop: StopCandidate
    walk: WalkEstimate
    eta: EtaEstimate
    slack_s: int | None
    feasible: bool
    risks: list[Risk]
    reason: str


class RecommendationResponse(BaseModel):
    at: TaipeiDatetime
    primary: RecommendationItem | None
    alternatives: list[RecommendationItem] = Field(max_length=2)
    message: str | None = None


class WalkRoute(WalkEstimate):
    coordinates: list[tuple[float, float]] = Field(description="[lon, lat] pairs (GeoJSON order)")


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=500)
    lat: Lat
    lon: Lon
    at: TaipeiDatetime | None = None


class ChatResponse(BaseModel):
    reply: str
    tool_results: list[dict]
    at: TaipeiDatetime


class HealthResponse(BaseModel):
    status: Literal["ok"]
    db: Literal["ok", "error"]
    latest_gps_at: TaipeiDatetime | None


class ErrorBody(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorBody

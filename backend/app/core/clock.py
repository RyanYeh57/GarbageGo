from datetime import datetime
from zoneinfo import ZoneInfo

TAIPEI = ZoneInfo("Asia/Taipei")


def to_taipei(dt: datetime) -> datetime:
    """Return dt in Taipei time. A naive dt is read as Taipei time, not UTC."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=TAIPEI)
    return dt.astimezone(TAIPEI)


def resolve_at(at: datetime | None) -> datetime:
    """API-layer helper: the request's `at`, or now when not given. Modules take this as a parameter."""
    return datetime.now(TAIPEI) if at is None else to_taipei(at)


def parse_taichung_time(s: str) -> datetime:
    """'20261103T193953' (Taichung API, no zone) -> Taipei-aware datetime. Bad format -> ValueError."""
    if not isinstance(s, str) or len(s) != 15:
        raise ValueError(f"not a YYYYMMDDTHHMMSS time: {s!r}")
    return datetime.strptime(s, "%Y%m%dT%H%M%S").replace(tzinfo=TAIPEI)

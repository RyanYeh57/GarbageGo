from datetime import datetime, timezone

from app.core.clock import TAIPEI, to_taipei


def test_to_taipei_converts_aware_time():
    got = to_taipei(datetime(2026, 11, 23, 11, 0, tzinfo=timezone.utc))
    assert got == datetime(2026, 11, 23, 19, 0, tzinfo=TAIPEI)
    assert got.utcoffset().total_seconds() == 8 * 3600


def test_to_taipei_reads_naive_time_as_taipei():
    got = to_taipei(datetime(2026, 11, 23, 19, 0))
    assert got.isoformat() == "2026-11-23T19:00:00+08:00"

"""Week-1 fake data so the Android app can start before the real modules exist.

Everything here is made up (addresses say 示範路, plates say TEST). Replace endpoint by endpoint:
stops/routes -> backend A, eta -> backend B, recommendations/chat -> architect.
"""

from datetime import datetime, time, timedelta

from app.api.schemas import (
    ChatResponse,
    EtaEstimate,
    EtaStatus,
    GeocodeLevel,
    RecommendationItem,
    RecommendationResponse,
    ScheduleSlot,
    StopCandidate,
    StopDetail,
    WalkEstimate,
    WalkRoute,
    WasteKind,
    WeeklySlot,
)

FAKE_NOTE = "[假資料] "

# id -> (lat, lon, geocode_level, today's general-waste slot, distance_m, eta status)
_STOPS = {
    1001: (24.1481, 120.6742, GeocodeLevel.exact, (time(19, 0), time(19, 10)), 75, EtaStatus.live),
    1002: (24.1469, 120.6751, GeocodeLevel.approx_nearby_number, (time(19, 20), time(19, 30)), 180, EtaStatus.stale),
    1003: (24.1490, 120.6720, GeocodeLevel.exact, (time(19, 40), time(19, 50)), 220, EtaStatus.schedule_only),
}


def _today_slots(stop_id: int) -> list[ScheduleSlot]:
    start, end = _STOPS[stop_id][3]
    return [
        ScheduleSlot(kind=WasteKind.general, start=start, end=end),
        ScheduleSlot(kind=WasteKind.recycle, start=start, end=end),
    ]


def has_stop(stop_id: int) -> bool:
    return stop_id in _STOPS


def nearby_stops() -> list[StopCandidate]:
    return [
        StopCandidate(
            id=stop_id,
            area="西區",
            village="示範里",
            address=f"臺中市西區示範路{n}號",
            lat=lat,
            lon=lon,
            geocode_level=level,
            today_slots=_today_slots(stop_id),
            distance_m=distance,
        )
        for n, (stop_id, (lat, lon, level, _, distance, _)) in enumerate(_STOPS.items(), start=1)
    ]


def stop_detail(stop_id: int) -> StopDetail:
    stop = next(s for s in nearby_stops() if s.id == stop_id)
    start, end = _STOPS[stop_id][3]
    weekly = [WeeklySlot(weekday=d, kind=WasteKind.general, start=start, end=end) for d in (1, 2, 4, 5, 6)]
    weekly += [WeeklySlot(weekday=d, kind=WasteKind.recycle, start=start, end=end) for d in (1, 5)]
    return StopDetail(**stop.model_dump(exclude={"today_slots", "distance_m"}), car_licence="TEST-0001", weekly=weekly)


def stop_eta(stop_id: int, at: datetime) -> EtaEstimate:
    start_t, end_t = _STOPS[stop_id][3]
    status = _STOPS[stop_id][5]
    start = datetime.combine(at.date(), start_t, tzinfo=at.tzinfo)
    end = datetime.combine(at.date(), end_t, tzinfo=at.tzinfo)
    if status is EtaStatus.live:
        eta = start + timedelta(minutes=3)
        return EtaEstimate(
            status=status, eta=eta, eta_low=eta - timedelta(minutes=2), eta_high=eta + timedelta(minutes=5),
            data_time=at - timedelta(minutes=2), scheduled_start=start, scheduled_end=end, method="distance_speed",
        )
    # stale / schedule_only: fall back to the scheduled slot (backend-architecture.md §4)
    data_time = at - timedelta(minutes=40) if status is EtaStatus.stale else None
    return EtaEstimate(
        status=status, eta=start + (end - start) / 2, eta_low=start, eta_high=end,
        data_time=data_time, scheduled_start=start, scheduled_end=end, method="schedule",
    )


def recommendation(at: datetime) -> RecommendationResponse:
    stops = {s.id: s for s in nearby_stops()}
    primary = RecommendationItem(
        stop=stops[1001],
        walk=WalkEstimate(duration_s=90, distance_m=75, method="valhalla"),
        eta=stop_eta(1001, at),
        slack_s=600,
        feasible=True,
        risks=[],
        reason=FAKE_NOTE + "走路 2 分鐘，車子用即時 GPS 估計，時間最寬裕。",
    )
    backup = RecommendationItem(
        stop=stops[1003],
        walk=WalkEstimate(duration_s=200, distance_m=220, method="valhalla"),
        eta=stop_eta(1003, at),
        slack_s=1500,
        feasible=True,
        risks=["schedule_only"],
        reason=FAKE_NOTE + "備案：只有表定時間，沒有即時 GPS。",
    )
    return RecommendationResponse(at=at, primary=primary, alternatives=[backup])


def walk_route(from_lat: float, from_lon: float, to_lat: float, to_lon: float) -> WalkRoute:
    mid = ((from_lon + to_lon) / 2, (from_lat + to_lat) / 2)
    return WalkRoute(
        duration_s=300, distance_m=350, method="fallback",
        coordinates=[(from_lon, from_lat), mid, (to_lon, to_lat)],
    )


def chat(at: datetime) -> ChatResponse:
    return ChatResponse(reply=FAKE_NOTE + "這是第 1 週的固定回答，之後會換成真的 AI 助理。", tool_results=[], at=at)

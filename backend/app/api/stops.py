from fastapi import APIRouter, HTTPException, Query

from app.api import fixtures
from app.api.schemas import AtQuery, EtaEstimate, ErrorResponse, LatQuery, LonQuery, StopCandidate, StopDetail
from app.core.clock import resolve_at

router = APIRouter(prefix="/stops", tags=["stops"])

NOT_FOUND = {404: {"model": ErrorResponse, "description": "`stop_not_found`"}}


def _require_stop(stop_id: int) -> None:
    if not fixtures.has_stop(stop_id):
        raise HTTPException(status_code=404, detail="stop_not_found")


@router.get("/nearby", response_model=list[StopCandidate])
def nearby(lat: LatQuery, lon: LonQuery, radius: int = Query(500, ge=100, le=2000), at: AtQuery = None):
    return fixtures.nearby_stops()


@router.get("/{stop_id}", response_model=StopDetail, responses=NOT_FOUND)
def stop(stop_id: int):
    _require_stop(stop_id)
    return fixtures.stop_detail(stop_id)


@router.get("/{stop_id}/eta", response_model=EtaEstimate, responses=NOT_FOUND)
def stop_eta(stop_id: int, at: AtQuery = None):
    _require_stop(stop_id)
    return fixtures.stop_eta(stop_id, resolve_at(at))

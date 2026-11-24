from fastapi import APIRouter

from app.api import fixtures
from app.api.schemas import LatQuery, LonQuery, WalkRoute

router = APIRouter(prefix="/routes", tags=["routes"])


@router.get("/walk", response_model=WalkRoute)
def walk(from_lat: LatQuery, from_lon: LonQuery, to_lat: LatQuery, to_lon: LonQuery):
    return fixtures.walk_route(from_lat, from_lon, to_lat, to_lon)

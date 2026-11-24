from fastapi import APIRouter

from app.api import fixtures
from app.api.schemas import RecommendationRequest, RecommendationResponse
from app.core.clock import resolve_at

router = APIRouter(tags=["recommendations"])


@router.post("/recommendations", response_model=RecommendationResponse)
def recommend(req: RecommendationRequest):
    return fixtures.recommendation(resolve_at(req.at))

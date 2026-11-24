from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.schemas import HealthResponse
from app.db.session import get_session

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(session: Session = Depends(get_session)) -> HealthResponse:
    try:
        session.execute(text("SELECT 1"))
        db = "ok"
    except Exception:  # /health must answer even when the database is down
        db = "error"
    return HealthResponse(status="ok", db=db, latest_gps_at=None)

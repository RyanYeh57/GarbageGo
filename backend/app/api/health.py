from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_session

router = APIRouter()


@router.get("/health")
def health(session: Session = Depends(get_session)) -> dict:
    try:
        session.execute(text("SELECT 1"))
        db = "ok"
    except Exception:  # /health must answer even when the database is down
        db = "error"
    return {"status": "ok", "db": db, "latest_gps_at": None}

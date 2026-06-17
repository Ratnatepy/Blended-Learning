"""FastAPI application entrypoint."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.core.config import get_api_config
from api.database import Base, SessionLocal, engine
from api.routes import recommendations, students
from api.seed import seed_student_recommendations


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create tables and seed data during application startup."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_student_recommendations(db)
    finally:
        db.close()
    yield


app_cfg = get_api_config().get("app", {})
app = FastAPI(
    title=app_cfg.get("title", "Blended Learning Recommendation API"),
    description=app_cfg.get(
        "description",
        "FastAPI backend for student segmentation and personalized recommendation prototype",
    ),
    version=app_cfg.get("version", "1.0.0"),
    lifespan=lifespan,
)

app.include_router(students.router, prefix="/students", tags=["Students"])
app.include_router(recommendations.router, prefix="/recommendations", tags=["Recommendations"])


@app.get("/")
def root():
    return {
        "message": "Blended Learning Recommendation API is running",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health_check():
    return {"status": "ok"}

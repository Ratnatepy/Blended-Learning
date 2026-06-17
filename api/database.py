"""Database session setup for the FastAPI backend."""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from api.core.config import env_value, get_api_config

api_cfg = get_api_config()
database_cfg = api_cfg.get("database", {})

DATABASE_URL = env_value(
    database_cfg.get("env", "DATABASE_URL"),
    database_cfg.get("default_url"),
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=bool(database_cfg.get("pool_pre_ping", True)),
    echo=bool(database_cfg.get("echo", False)),
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Yield one SQLAlchemy session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

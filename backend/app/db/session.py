"""Database session factory."""

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.app.core.config import get_settings


def build_session_factory(database_url: str | None = None) -> sessionmaker[Session]:
    """Create a non-global session factory, convenient for scripts and tests."""

    engine = create_engine(database_url or get_settings().database_url, pool_pre_ping=True)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

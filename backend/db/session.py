from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from ..config import get_settings

settings = get_settings()

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""


def get_session() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session."""
    session: Session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

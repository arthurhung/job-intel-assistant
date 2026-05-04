from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from job_intel.db.models import Base


def create_db_engine(db_path: Path) -> Engine:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{db_path}", future=True)
    Base.metadata.create_all(engine)
    return engine


def create_session_factory(db_path: Path) -> sessionmaker[Session]:
    engine = create_db_engine(db_path)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)


def connect(db_path: Path) -> Session:
    return create_session_factory(db_path)()


@contextmanager
def session(db_path: Path) -> Iterator[Session]:
    engine = create_db_engine(db_path)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)
    db_session = factory()
    try:
        yield db_session
    finally:
        db_session.close()
        engine.dispose()

"""Test configuration for the HackerNews Viewer backend."""
import os
import sys
import pytest
import asyncio
from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy.pool import StaticPool

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import get_db


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_db():
    """Create a test database."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    SQLModel.metadata.create_all(engine)
    
    def get_session():
        with Session(engine) as session:
            yield session
    
    return get_session


@pytest.fixture
def db_session(test_db):
    """Get a database session for testing."""
    session = next(test_db())
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def override_get_db(db_session):
    """Override the get_db dependency."""
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    return _override_get_db

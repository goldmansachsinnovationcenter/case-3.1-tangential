"""Database connection and session management."""
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.pool import StaticPool

from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)



def get_db():
    """Get database session."""
    with Session(engine) as session:
        try:
            yield session
        finally:
            session.close()

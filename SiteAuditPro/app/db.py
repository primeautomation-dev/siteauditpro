from sqlmodel import SQLModel, create_engine, Session
from app.models import Audit

# Database file path
DATABASE_URL = "sqlite:///./siteaudit.db"

# Create engine
engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})


def init_db():
    """Initialize the database and create tables."""
    # Drop all tables and recreate to ensure schema matches models
    # This ensures the database schema always matches the current model definitions
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)


def get_session():
    """Get a database session."""
    return Session(engine)


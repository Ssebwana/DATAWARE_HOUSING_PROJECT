"""
MakFleet Prototype - Database Configuration
Uses SQLite for demonstration (no PostgreSQL required)
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Use SQLite for demonstration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///makfleet.db"
)

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()


def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables"""
    from .models import Driver, Vehicle, Telemetry, Event, Location
    Base.metadata.create_all(bind=engine)
    print("Database tables created")


def clear_telemetry_and_events():
    """Clear all telemetry and events data - call this on server startup
    to ensure vehicles/events don't appear until simulator is running"""
    from .models import Telemetry, Event
    db = SessionLocal()
    try:
        # Delete all telemetry and events (keep drivers, vehicles, locations)
        db.query(Telemetry).delete()
        db.query(Event).delete()
        db.commit()
        print("Cleared old telemetry and event data")
    except Exception as e:
        print(f"Error clearing data: {e}")
        db.rollback()
    finally:
        db.close()

"""
MakFleet Prototype - Database Models
SQLAlchemy models for the data warehouse (SQLite compatible)
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


class Driver(Base):
    """Driver model"""
    __tablename__ = "drivers"

    driver_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(20))
    license_number = Column(String(50), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    vehicles = relationship("Vehicle", back_populates="driver")


class Vehicle(Base):
    """Vehicle model"""
    __tablename__ = "vehicles"

    vehicle_id = Column(Integer, primary_key=True, index=True)
    plate_number = Column(String(20), unique=True, nullable=False)
    driver_id = Column(Integer, ForeignKey("drivers.driver_id"))
    model = Column(String(50))
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    driver = relationship("Driver", back_populates="vehicles")
    telemetry = relationship("Telemetry", back_populates="vehicle")
    events = relationship("Event", back_populates="vehicle")


class Telemetry(Base):
    """Telemetry data model - stores raw IoT sensor data"""
    __tablename__ = "telemetry"

    telemetry_id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.vehicle_id"), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    speed = Column(Float, nullable=False)
    acceleration = Column(Float)
    engine_temp = Column(Float)
    fuel_level = Column(Float)
    timestamp = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    vehicle = relationship("Vehicle", back_populates="telemetry")


class Event(Base):
    """Event model - stores detected events from telemetry"""
    __tablename__ = "events"

    event_id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.vehicle_id"), nullable=False)
    event_type = Column(String(50), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    speed = Column(Float)
    acceleration = Column(Float)
    timestamp = Column(DateTime, nullable=False)
    severity = Column(String(20), default="medium")
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    vehicle = relationship("Vehicle", back_populates="events")


class Location(Base):
    """Location model - campus zones"""
    __tablename__ = "locations"

    location_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    zone = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)

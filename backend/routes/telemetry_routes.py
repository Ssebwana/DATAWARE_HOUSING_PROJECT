"""
MakFleet Prototype - Telemetry Routes
API endpoints for telemetry data ingestion and retrieval
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

from ..database import get_db
from ..models import Telemetry, Vehicle, Driver
from ..services.event_detection import EventDetectionService
from ..services.analytics import AnalyticsService


router = APIRouter(prefix="/api/telemetry", tags=["telemetry"])


# Pydantic schemas for request/response
class TelemetryCreate(BaseModel):
    vehicle_id: int
    latitude: float
    longitude: float
    speed: float
    acceleration: float
    engine_temp: Optional[float] = None
    fuel_level: Optional[float] = None
    timestamp: Optional[datetime] = None


class TelemetryResponse(BaseModel):
    telemetry_id: int
    vehicle_id: int
    latitude: float
    longitude: float
    speed: float
    acceleration: Optional[float]
    engine_temp: Optional[float]
    fuel_level: Optional[float]
    timestamp: datetime

    class Config:
        from_attributes = True


@router.post("/", status_code=status.HTTP_201_CREATED)
def add_telemetry(
    data: TelemetryCreate,
    db: Session = Depends(get_db)
):
    """
    Ingest telemetry data from IoT devices
    
    This endpoint receives raw telemetry data from GPS/sensors,
    stores it in the database, and triggers event detection.
    """
    # Validate vehicle exists
    vehicle = db.query(Vehicle).filter(Vehicle.vehicle_id == data.vehicle_id).first()
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vehicle with ID {data.vehicle_id} not found"
        )
    
    # Use current timestamp if not provided
    timestamp = data.timestamp or datetime.utcnow()
    
    # Create telemetry record
    telemetry = Telemetry(
        vehicle_id=data.vehicle_id,
        latitude=data.latitude,
        longitude=data.longitude,
        speed=data.speed,
        acceleration=data.acceleration,
        engine_temp=data.engine_temp,
        fuel_level=data.fuel_level,
        timestamp=timestamp
    )
    
    db.add(telemetry)
    db.commit()
    db.refresh(telemetry)
    
    # Detect events from this telemetry data
    event_type, severity = EventDetectionService.detect_event(
        speed=data.speed,
        acceleration=data.acceleration
    )
    
    if event_type:
        from ..models import Event
        event = Event(
            vehicle_id=data.vehicle_id,
            event_type=event_type,
            latitude=data.latitude,
            longitude=data.longitude,
            speed=data.speed,
            acceleration=data.acceleration,
            timestamp=timestamp,
            severity=severity
        )
        db.add(event)
        db.commit()
    
    return {
        "status": "stored",
        "telemetry_id": telemetry.telemetry_id,
        "event_detected": event_type
    }


@router.get("/recent")
def get_recent_telemetry(
    vehicle_id: Optional[int] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get recent telemetry readings
    
    Args:
        vehicle_id: Optional filter by vehicle
        limit: Maximum number of records to return
    """
    return AnalyticsService.get_recent_telemetry(db, vehicle_id, limit)


@router.get("/summary/{vehicle_id}")
def get_telemetry_summary(
    vehicle_id: int,
    hours: int = 24,
    db: Session = Depends(get_db)
):
    """
    Get telemetry summary for a vehicle
    
    Args:
        vehicle_id: Vehicle ID
        hours: Number of hours to look back
    """
    return AnalyticsService.get_vehicle_telemetry_summary(db, vehicle_id, hours)


@router.get("/latest")
def get_latest_telemetry(
    db: Session = Depends(get_db)
):
    """
    Get the latest telemetry reading for each vehicle
    """
    # Get all telemetry ordered by vehicle and timestamp
    telemetry = db.query(Telemetry).order_by(
        Telemetry.vehicle_id, Telemetry.timestamp.desc()
    ).all()
    
    # Get latest per vehicle
    latest_by_vehicle = {}
    for t in telemetry:
        if t.vehicle_id not in latest_by_vehicle:
            # Get vehicle info
            vehicle = db.query(Vehicle).filter(Vehicle.vehicle_id == t.vehicle_id).first()
            driver_name = "Unknown"
            if vehicle and vehicle.driver_id:
                driver = db.query(Driver).filter(Driver.driver_id == vehicle.driver_id).first()
                if driver:
                    driver_name = driver.name
            
            latest_by_vehicle[t.vehicle_id] = {
                "vehicle_id": t.vehicle_id,
                "plate_number": vehicle.plate_number if vehicle else "Unknown",
                "driver_name": driver_name,
                "latitude": t.latitude,
                "longitude": t.longitude,
                "speed": t.speed,
                "acceleration": t.acceleration,
                "engine_temp": t.engine_temp,
                "fuel_level": t.fuel_level,
                "timestamp": t.timestamp.isoformat() if t.timestamp else None
            }
    
    return list(latest_by_vehicle.values())

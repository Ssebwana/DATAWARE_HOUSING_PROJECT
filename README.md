# MakFleet Spatio-Temporal Data Warehouse Prototype

A working prototype demonstrating the core concept of a Spatio-Temporal Data Warehouse for MakFleet bodaboda tracking system at Makerere University.

## Architecture Overview

```
IoT Device / Simulator
        ↓
Data Ingestion API (FastAPI)
        ↓
Database (PostgreSQL + PostGIS)
        ↓
Event Processing
        ↓
Dashboard / BI Visualization
```

## Project Structure

```
makfleet-prototype/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── database.py          # Database configuration
│   ├── models.py            # SQLAlchemy models
│   ├── routes/
│   │   ├── telemetry_routes.py
│   │   ├── event_routes.py
│   │   └── vehicle_routes.py
│   └── services/
│       ├── event_detection.py
│       └── analytics.py
├── simulator/
│   └── iot_simulator.py    # IoT data simulator
├── dashboard/
│   ├── index.html          # Main dashboard
│   ├── map.js              # Map visualization
│   └── charts.js           # Chart visualizations
├── database/
│   └── schema.sql          # Database schema
└── requirements.txt        # Python dependencies
```

## Prerequisites

1. **PostgreSQL** with PostGIS extension
2. **Python 3.8+**
3. **Node.js** (optional, for production)

## Setup Instructions

### 1. Database Setup

```bash
# Create database
createdb makfleet

# Enable PostGIS
psql -d makfleet -c "CREATE EXTENSION IF NOT EXISTS postgis;"

# Run schema
psql -d makfleet -f database/schema.sql
```

### 2. Backend Setup

```bash
# Navigate to project directory
cd makfleet-prototype

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables (optional)
export DATABASE_URL="postgresql://postgres:password@localhost:5432/makfleet"

# Run the API server
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at: http://localhost:8000

### 3. IoT Simulator

```bash
# Run the simulator (in a new terminal)
python simulator/iot_simulator.py -n 5

# This will send simulated telemetry data every 3 seconds
```

### 4. Dashboard

Open the dashboard in your browser:
```
http://localhost:8000/dashboard
```

Or open `dashboard/index.html` directly in a browser (requires API to be running).

## API Endpoints

### Telemetry
- `POST /api/telemetry` - Ingest telemetry data
- `GET /api/telemetry/recent` - Get recent telemetry
- `GET /api/telemetry/latest` - Get latest reading per vehicle

### Events
- `GET /api/events` - Get events with filters
- `GET /api/events/summary` - Get event summary
- `GET /api/events/dangerous-zones` - Get dangerous zones
- `GET /api/events/driver-risk` - Get driver risk scores

### Vehicles
- `GET /api/vehicles` - Get all vehicles
- `GET /api/vehicles/{id}` - Get specific vehicle
- `POST /api/vehicles` - Create new vehicle
- `GET /api/vehicles/drivers/` - Get all drivers

## Event Detection Rules

| Event Type | Condition | Severity |
|------------|-----------|----------|
| HARSH_BRAKING | acceleration < -4 m/s² | High/Medium |
| RAPID_ACCELERATION | acceleration > 4 m/s² | High/Medium |
| OVERSPEED | speed > 70 km/h | High/Medium |
| IDLING | speed = 0, acceleration = 0 | Low |

## Risk Score Formula

```
Risk Score = (Harsh Braking × 3) + (Overspeed × 2) + (Rapid Acceleration × 1) + (Idling × 0.5)
```

## Technology Stack

| Component | Technology |
|-----------|------------|
| Backend API | FastAPI (Python) |
| Database | PostgreSQL + PostGIS |
| Data Processing | Python |
| Dashboard | HTML + JavaScript |
| Map Visualization | Leaflet.js |
| Charts | Chart.js |

## Features Demonstrated

✅ IoT telemetry simulation  
✅ Data ingestion API  
✅ Telemetry storage  
✅ Event detection (harsh braking, speeding, etc.)  
✅ Map visualization (vehicle positions, event markers)  
✅ Basic dashboard analytics  
✅ Driver risk scoring  

## Optional Advanced Features

- [ ] Heatmap of dangerous areas
- [ ] Driver risk score
- [ ] Route replay
- [ ] Anomaly detection model
- [ ] Neo4j knowledge graph

## Troubleshooting

### Database Connection Error
Make sure PostgreSQL is running and the connection string is correct in `backend/database.py`.

### API Not Responding
Check if port 8000 is available. Try running on a different port:
```bash
uvicorn backend.main:app --port 8001
```

### Dashboard Not Loading
Ensure the API is running and accessible. Check browser console for errors.

## License

This is a prototype for educational purposes.

"""
MakFleet Prototype - Main FastAPI Application
Spatio-Temporal Data Warehouse for MakFleet

This is the backend API for the prototype that demonstrates:
- IoT telemetry ingestion
- Event detection
- Analytics and dashboard
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import os

from .database import init_db, clear_telemetry_and_events
from .routes import telemetry_routes, event_routes, vehicle_routes


# Create FastAPI app
app = FastAPI(
    title="MakFleet Spatio-Temporal Data Warehouse",
    description="Prototype API for MakFleet bodaboda tracking system",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(telemetry_routes.router)
app.include_router(event_routes.router)
app.include_router(vehicle_routes.router)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup and clear old telemetry/events"""
    init_db()
    clear_telemetry_and_events()
    print("Database initialized and old telemetry/events cleared")


@app.get("/", response_class=HTMLResponse)
def root():
    """Root endpoint - redirects to dashboard"""
    # Get the base directory (makfleet-prototype)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dashboard_path = os.path.join(base_dir, "dashboard", "index.html")
    
    if os.path.exists(dashboard_path):
        with open(dashboard_path, "r") as f:
            return f.read()
    else:
        return """
        <html>
            <head>
                <title>MakFleet Dashboard</title>
                <script src="https://cdn.tailwindcss.com"></script>
            </head>
            <body class="bg-gray-100 flex items-center justify-center min-h-screen">
                <div class="text-center">
                    <h1 class="text-2xl font-bold text-gray-800 mb-4">MakFleet Dashboard</h1>
                    <p class="text-gray-600">Loading...</p>
                </div>
            </body>
        </html>
        """


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


# Dashboard - serve static HTML
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """Serve the dashboard HTML"""
    # Get the base directory (makfleet-prototype)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dashboard_path = os.path.join(base_dir, "dashboard", "index.html")
    
    print(f"Looking for dashboard at: {dashboard_path}")
    
    if os.path.exists(dashboard_path):
        with open(dashboard_path, "r") as f:
            return f.read()
    else:
        return """
        <html>
            <head>
                <title>MakFleet Dashboard</title>
                <script src="https://cdn.tailwindcss.com"></script>
            </head>
            <body class="bg-gray-100 flex items-center justify-center min-h-screen">
                <div class="text-center">
                    <h1 class="text-2xl font-bold text-gray-800 mb-4">MakFleet Dashboard</h1>
                    <p class="text-gray-600">Dashboard file not found at: """ + dashboard_path + """</p>
                </div>
            </body>
        </html>
        """


# Mount static files
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
static_path = os.path.join(base_dir, "dashboard")
if os.path.exists(static_path):
    app.mount("/static", StaticFiles(directory=static_path), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

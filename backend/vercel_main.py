"""
MakFleet Backend - Vercel Serverless Version
Simplified version for Vercel deployment with only essential functionality
Note: Uses in-memory storage since Vercel serverless doesn't persist files
"""
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional, Dict
import hashlib
import json

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "makfleet-secret-key-change-in-production-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Simple password hashing
def hash_password(password: str) -> str:
    """Hash password using SHA-256 with salt"""
    salt = "makfleet_salt_2026"
    return hashlib.sha256(f"{password}{salt}".encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password"""
    return hash_password(plain_password) == hashed_password

# Simple token implementation
def create_access_token(data: dict) -> str:
    """Create a simple token (base64 encoded JSON)"""
    import base64
    data["exp"] = (datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)).isoformat()
    token = base64.b64encode(json.dumps(data).encode()).decode()
    return token

def decode_token(token: str) -> Optional[dict]:
    """Decode a simple token"""
    try:
        import base64
        data = json.loads(base64.b64decode(token).decode())
        if datetime.fromisoformat(data["exp"]) < datetime.utcnow():
            return None
        return data
    except:
        return None

# In-memory user storage (for demo - use real DB in production)
# In a real app, you'd use PostgreSQL, MongoDB, or similar
users_db: Dict[str, dict] = {
    "admin": {
        "id": 1,
        "username": "admin",
        "email": "admin@makfleet.ac.ug",
        "hashed_password": hash_password("admin123"),
        "full_name": "System Administrator",
        "role": "admin",
        "is_active": True
    },
    "driver": {
        "id": 2,
        "username": "driver",
        "email": "driver@makfleet.ac.ug",
        "hashed_password": hash_password("driver123"),
        "full_name": "Demo Driver",
        "role": "driver",
        "is_active": True
    }
}

# Pydantic models
class UserLogin(BaseModel):
    username: str
    password: str

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    full_name: str
    role: str = "driver"
    driver_license: Optional[str] = None

# Create FastAPI app
app = FastAPI(title="MakFleet AI", description="Intelligent Semantic AI System")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
@app.get("/")
def root():
    """Root endpoint - redirect to login"""
    return FileResponse("dashboard/login.html")

@app.get("/login")
def login_page():
    """Login page"""
    return FileResponse("dashboard/login.html")

@app.get("/signup")
def signup_page():
    """Signup page"""
    return FileResponse("dashboard/signup.html")

@app.get("/dashboard")
def dashboard_page():
    """Dashboard page"""
    return FileResponse("dashboard/index.html")

@app.post("/api/auth/login")
def login(user_data: UserLogin):
    """Authenticate user and return token"""
    user = users_db.get(user_data.username)
    
    if not user or not user["is_active"]:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password"
        )
    
    if not verify_password(user_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password"
        )
    
    # Create token
    access_token = create_access_token({
        "sub": user["username"],
        "role": user["role"]
    })
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "full_name": user["full_name"],
            "role": user["role"],
            "is_active": user["is_active"]
        }
    }

@app.post("/api/auth/register")
def register(user_data: UserCreate):
    """Register a new user"""
    # Check if user exists
    if user_data.username in users_db:
        raise HTTPException(
            status_code=400,
            detail="Username already registered"
        )
    
    # Check if email is used
    for u in users_db.values():
        if u["email"] == user_data.email:
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )
    
    # Create new user
    new_id = max(u["id"] for u in users_db.values()) + 1
    new_user = {
        "id": new_id,
        "username": user_data.username,
        "email": user_data.email,
        "hashed_password": hash_password(user_data.password),
        "full_name": user_data.full_name,
        "role": user_data.role,
        "is_active": True
    }
    
    users_db[user_data.username] = new_user
    
    # Create token
    access_token = create_access_token({
        "sub": new_user["username"],
        "role": new_user["role"]
    })
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": new_user["id"],
            "username": new_user["username"],
            "email": new_user["email"],
            "full_name": new_user["full_name"],
            "role": new_user["role"],
            "is_active": True
        }
    }

@app.get("/api/auth/me")
def get_profile(token: str):
    """Get current user profile"""
    data = decode_token(token)
    if not data:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    user = users_db.get(data["sub"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "id": user["id"],
        "username": user["username"],
        "email": user["email"],
        "full_name": user["full_name"],
        "role": user["role"],
        "is_active": user["is_active"]
    }

# Static files
app.mount("/static", StaticFiles(directory="dashboard"), name="static")

# Catch-all for SPA routing
@app.get("/{path:path}")
def catch_all(path: str):
    """Serve dashboard for all other routes"""
    return FileResponse("dashboard/index.html")
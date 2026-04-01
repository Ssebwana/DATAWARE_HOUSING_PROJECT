"""
MakFleet Backend - Vercel Serverless Version
Simplified version for Vercel deployment with only essential functionality
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
from typing import Optional
import sqlite3
import hashlib
import secrets
import json

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "makfleet-secret-key-change-in-production-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours
DATABASE_PATH = os.path.join(os.path.dirname(__file__), "..", "makfleet.db")

# Simple password hashing (for Vercel compatibility - no passlib needed)
def hash_password(password: str) -> str:
    """Hash password using SHA-256 with salt"""
    salt = "makfleet_salt_2026"
    return hashlib.sha256(f"{password}{salt}".encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password"""
    return hash_password(plain_password) == hashed_password

# Simple JWT implementation (for Vercel compatibility - no python-jose needed)
def create_access_token(data: dict) -> str:
    """Create a simple token (base64 encoded JSON for demo)"""
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

# Database setup
def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Initialize database with users table"""
    db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'driver',
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            driver_license TEXT
        )
    """)
    # Create default users if they don't exist
    try:
        db.execute("""
            INSERT OR IGNORE INTO users (username, email, hashed_password, full_name, role, is_active)
            VALUES ('admin', 'admin@makfleet.ac.ug', ?, 'System Administrator', 'admin', 1)
        """, (hash_password("admin123"),))
        db.execute("""
            INSERT OR IGNORE INTO users (username, email, hashed_password, full_name, role, is_active, driver_license)
            VALUES ('driver', 'driver@makfleet.ac.ug', ?, 'Demo Driver', 'driver', 1, 'UGA-DL-001234')
        """, (hash_password("driver123"),))
        db.commit()
    except Exception as e:
        print(f"Error initializing users: {e}")
    finally:
        db.close()

# Initialize database on startup
init_database()

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
    db = get_db()
    try:
        user = db.execute(
            "SELECT * FROM users WHERE username = ? AND is_active = 1",
            (user_data.username,)
        ).fetchone()
        
        if not user or not verify_password(user_data.password, user["hashed_password"]):
            raise HTTPException(
                status_code=401,
                detail="Incorrect username or password"
            )
        
        # Update last login
        db.execute("UPDATE users SET last_login = ? WHERE id = ?", 
                  (datetime.utcnow().isoformat(), user["id"]))
        db.commit()
        
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
                "is_active": bool(user["is_active"])
            }
        }
    finally:
        db.close()

@app.post("/api/auth/register")
def register(user_data: UserCreate):
    """Register a new user"""
    db = get_db()
    try:
        # Check if user exists
        existing = db.execute(
            "SELECT id FROM users WHERE username = ? OR email = ?",
            (user_data.username, user_data.email)
        ).fetchone()
        
        if existing:
            raise HTTPException(
                status_code=400,
                detail="Username or email already registered"
            )
        
        # Create user
        db.execute("""
            INSERT INTO users (username, email, hashed_password, full_name, role, driver_license)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            user_data.username,
            user_data.email,
            hash_password(user_data.password),
            user_data.full_name,
            user_data.role,
            user_data.driver_license
        ))
        db.commit()
        
        # Get created user
        user = db.execute(
            "SELECT * FROM users WHERE username = ?",
            (user_data.username,)
        ).fetchone()
        
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
                "is_active": True
            }
        }
    finally:
        db.close()

@app.get("/api/auth/me")
def get_profile(token: str):
    """Get current user profile"""
    data = decode_token(token)
    if not data:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    db = get_db()
    try:
        user = db.execute(
            "SELECT * FROM users WHERE username = ?",
            (data["sub"],)
        ).fetchone()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "full_name": user["full_name"],
            "role": user["role"],
            "is_active": bool(user["is_active"])
        }
    finally:
        db.close()

# Static files
app.mount("/static", StaticFiles(directory="dashboard"), name="static")

# Catch-all for SPA routing
@app.get("/{path:path}")
def catch_all(path: str):
    """Serve dashboard for all other routes"""
    return FileResponse("dashboard/index.html")
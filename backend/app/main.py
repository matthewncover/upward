from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import json
from pathlib import Path
from .database import create_db_and_tables, get_session
from .models import Habit
from .api import habits, scores, auth, whoop, notifications
from .config import settings
from sqlmodel import Session, select

app = FastAPI(title="Upward API", version="1.0.0")

# CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(habits.router)
app.include_router(scores.router)
app.include_router(auth.router)
app.include_router(whoop.router)
app.include_router(notifications.router)

# Serve static files (Vue frontend)
static_path = Path(__file__).parent.parent / "static"  # Go up one level to backend/static
if static_path.exists():
    # Mount static files at root for assets
    app.mount("/assets", StaticFiles(directory=str(static_path / "assets")), name="assets")
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

@app.on_event("startup")
async def startup_event():
    """Initialize database and load default habits."""
    create_db_and_tables()
    await load_default_habits()

@app.get("/")
async def serve_frontend():
    """Serve the Vue frontend."""
    static_index = Path(__file__).parent.parent / "static" / "index.html"
    if static_index.exists():
        return FileResponse(str(static_index))
    return {"message": "Upward API is running. Frontend not yet built."}

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "message": "Upward API is running"}

async def load_default_habits():
    """Load default habit configuration from JSON file."""
    config_path = Path(__file__).parent.parent / "config" / "habits.json"
    
    if not config_path.exists():
        print("No default habits configuration found")
        return
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        with next(get_session()) as session:
            # Check if habits already exist
            existing_habits = session.exec(select(Habit)).all()
            
            if existing_habits:
                print("Habits already exist, skipping default load")
                return
            
            # Load default habits
            for habit_data in config.get("habits", []):
                habit = Habit(**habit_data)
                session.add(habit)
            
            session.commit()
            print(f"Loaded {len(config.get('habits', []))} default habits")
    
    except Exception as e:
        print(f"Failed to load default habits: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
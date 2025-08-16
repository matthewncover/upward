#!/usr/bin/env python3
"""
Convenience script to run the Upward Habits application.
"""

import os
import sys
import subprocess
from pathlib import Path

def run_backend():
    """Run the FastAPI backend server."""
    backend_dir = Path(__file__).parent / "backend"
    os.chdir(backend_dir)
    
    # Add backend directory to Python path
    sys.path.insert(0, str(backend_dir))
    
    try:
        import uvicorn
        uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
    except ImportError:
        print("uvicorn not found. Installing dependencies...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        import uvicorn
        uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

def build_frontend():
    """Build the Vue.js frontend."""
    frontend_dir = Path(__file__).parent / "frontend"
    
    if not (frontend_dir / "node_modules").exists():
        print("Installing frontend dependencies...")
        subprocess.run(["npm.cmd", "install"], cwd=frontend_dir, check=True, shell=True)
    
    print("Building frontend...")
    subprocess.run(["npm.cmd", "run", "build"], cwd=frontend_dir, check=True, shell=True)
    print("Frontend built successfully!")

def setup_database():
    """Initialize the database with Alembic migrations."""
    try:
        subprocess.run(["alembic", "upgrade", "head"], check=True)
        print("Database initialized successfully!")
    except subprocess.CalledProcessError:
        print("Failed to initialize database. Make sure Alembic is installed.")
        sys.exit(1)

def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "build":
            build_frontend()
        elif command == "setup":
            setup_database()
        elif command == "dev":
            # Development mode - don't build frontend, assume it's running separately
            run_backend()
        else:
            print(f"Unknown command: {command}")
            print("Usage: python run.py [build|setup|dev]")
            sys.exit(1)
    else:
        # Default: build frontend and run backend
        build_frontend()
        run_backend()

if __name__ == "__main__":
    main()
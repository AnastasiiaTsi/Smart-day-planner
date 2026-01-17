import os
import sys
from pathlib import Path

# Додаємо кореневу папку проекту до Python path
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

# Імпортуємо наші модулі
from app.api.routes import router
from app.db.mongodb import connect_to_mongo, close_mongo_connection
from app.tasks.scheduler import start_scheduler
from app.core.logger import logger
from app.core.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"Starting {settings.APP_NAME}")
    await connect_to_mongo()
    
    # Start background scheduler
    scheduler = start_scheduler()
    
    yield
    
    # Shutdown
    logger.info(f"Shutting down {settings.APP_NAME}")
    await close_mongo_connection()
    if scheduler:
        scheduler.shutdown()

app = FastAPI(
    title="Smart Day Planner",
    description="A smart day planner that adapts to weather conditions",
    version="1.0.0",
    lifespan=lifespan
)

# Include API routes
app.include_router(router, prefix="/api/v1")

# Serve static files
app.mount("/static", StaticFiles(directory="app/frontend/static"), name="static")

@app.get("/")
async def read_root():
    """Serve the frontend"""
    from fastapi.responses import HTMLResponse
    try:
        with open("app/frontend/templates/index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Smart Day Planner</h1><p>Frontend template not found</p>")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Smart Day Planner"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse
import os

# Try to import our modules with fallbacks
try:
    from app.db.models import DayPlan, UserPreferences
    from app.weather.weather_api import WeatherAPI
    from app.weather.weather_station import WeatherStation
    from app.planner.day_planner import DayPlanner
    from app.core.logger import logger
    
    # Initialize services
    weather_api = WeatherAPI()
    weather_station = WeatherStation()
    day_planner = DayPlanner()
    
    # Attach day planner to weather station
    weather_station.attach(day_planner)
    
    MODULES_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Some modules not available: {e}")
    MODULES_AVAILABLE = False

router = APIRouter()

@router.get("/plan/current")
async def get_current_plan():
    """Get the current activity plan"""
    if not MODULES_AVAILABLE:
        return {"error": "Day planner module not available"}
    
    plan = await day_planner.get_current_plan()
    if not plan:
        raise HTTPException(status_code=404, detail="No plan available. Please update weather first.")
    return plan

@router.post("/weather/update")
async def update_weather(background_tasks: BackgroundTasks, city: str = "Berlin"):
    """Force a weather update"""
    if not MODULES_AVAILABLE:
        return {"error": "Weather module not available"}
    
    try:
        weather_data = await weather_api.get_weather_data(city)
        condition = weather_api.map_weather_condition(weather_data)
        
        processed_data = {
            "condition": condition,
            "temperature": weather_data["main"]["temp"],
            "humidity": weather_data["main"]["humidity"],
            "description": weather_data["weather"][0]["description"],
            "location": city
        }
        
        await weather_station.set_weather(processed_data, city)
        
        return {
            "message": f"Weather updated for {city}",
            "weather": processed_data
        }
    except Exception as e:
        logger.error(f"Error updating weather: {e}")
        raise HTTPException(status_code=500, detail="Failed to update weather")

@router.get("/plan/history")
async def get_plan_history(date: str = None, location: str = "Berlin"):
    """Get historical plans"""
    if not MODULES_AVAILABLE:
        return {"error": "Database module not available"}
    
    try:
        if not date:
            from datetime import datetime
            date = datetime.now().strftime("%Y-%m-%d")
            
        plan = await day_planner.get_plan_from_db(date, location)
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        return plan
    except Exception as e:
        logger.error(f"Error fetching plan history: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch plan history")

@router.post("/preferences")
async def update_preferences(preferences: dict):
    """Update user preferences"""
    if not MODULES_AVAILABLE:
        return {"error": "Day planner module not available"}
    
    try:
        from app.db.models import UserPreferences
        user_prefs = UserPreferences(**preferences)
        await day_planner.set_user_preferences(user_prefs)
        return {"message": "Preferences updated successfully"}
    except Exception as e:
        logger.error(f"Error updating preferences: {e}")
        raise HTTPException(status_code=500, detail="Failed to update preferences")

@router.get("/preferences")
async def get_preferences():
    """Get current user preferences"""
    if not MODULES_AVAILABLE:
        return {"error": "Day planner module not available"}
    
    return day_planner.user_preferences

@router.get("/")
async def read_root():
    """Serve the frontend"""
    try:
        with open("app/frontend/templates/index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Smart Day Planner</h1><p>Welcome to Smart Day Planner API. Use /docs for API documentation.</p>")
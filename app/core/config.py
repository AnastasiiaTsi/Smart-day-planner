import os

class Settings:
    APP_NAME: str = "Smart Day Planner"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # MongoDB
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://mongo:27017")
    MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME", "day_planner")
    
    # Weather API
    OPENWEATHER_API_KEY: str = os.getenv("OPENWEATHER_API_KEY", "demo_key_12345")
    OPENWEATHER_BASE_URL: str = "https://api.openweathermap.org/data/2.5"
    
    # Default location
    DEFAULT_CITY: str = os.getenv("DEFAULT_CITY", "Berlin")
    
    # Scheduling
    WEATHER_UPDATE_INTERVAL: int = int(os.getenv("WEATHER_UPDATE_INTERVAL", "1800"))

settings = Settings()
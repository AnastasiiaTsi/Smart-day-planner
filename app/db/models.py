from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class ActivityType(str, Enum):
    OUTDOOR = "outdoor"
    INDOOR = "indoor"
    PRODUCTIVE = "productive"
    RELAXATION = "relaxation"
    SPORT = "sport"
    LEARNING = "learning"

class WeatherCondition(str, Enum):
    SUNNY = "Sunny"
    RAINY = "Rainy"
    CLOUDY = "Cloudy"
    SNOWY = "Snowy"

class Activity(BaseModel):
    name: str
    type: ActivityType
    priority: int = Field(ge=1, le=5)
    description: Optional[str] = None

class UserPreferences(BaseModel):
    preferred_types: List[ActivityType] = []
    avoid_types: List[ActivityType] = []
    working_hours: Dict[str, int] = {"start": 9, "end": 17}
    weekend_mode: bool = True

class DayPlan(BaseModel):
    date: str
    location: str
    weather: Dict[str, Any]
    activities: List[Activity]
    user_id: str

class PlanDocument(DayPlan):
    model_config = ConfigDict(populate_by_name=True)
    
    id: Optional[str] = Field(None, alias='_id')
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
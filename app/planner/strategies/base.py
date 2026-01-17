from abc import ABC, abstractmethod
from typing import List
from app.db.models import Activity, UserPreferences

class WeatherStrategy(ABC):
    @abstractmethod
    async def get_activities(self, user_preferences: UserPreferences) -> List[Activity]:
        pass
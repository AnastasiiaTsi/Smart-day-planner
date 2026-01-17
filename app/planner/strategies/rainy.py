from app.planner.strategies.base import WeatherStrategy
from app.db.models import Activity, UserPreferences, ActivityType
from typing import List

class RainyWeatherStrategy(WeatherStrategy):
    async def get_activities(self, user_preferences: UserPreferences) -> List[Activity]:
        activities = [
            Activity(name="HouseWork", type=ActivityType.INDOOR, priority=5, description="Perfect day for indoor chores"),
            Activity(name="Studying", type=ActivityType.LEARNING, priority=4, description="Focus on learning activities"),
            Activity(name="Movie Marathon", type=ActivityType.RELAXATION, priority=3, description="Catch up on films"),
            Activity(name="Cooking", type=ActivityType.INDOOR, priority=3, description="Try new recipes"),
            Activity(name="Board Games", type=ActivityType.INDOOR, priority=2, description="Family game time"),
            Activity(name="Gym Workout", type=ActivityType.SPORT, priority=3, description="Indoor exercise"),
            Activity(name="Reading", type=ActivityType.RELAXATION, priority=2, description="Cozy reading time")
        ]
        
        return self._filter_activities(activities, user_preferences)
    
    def _filter_activities(self, activities: List[Activity], preferences: UserPreferences) -> List[Activity]:
        filtered = []
        
        for activity in activities:
            if activity.type in preferences.avoid_types:
                continue
                
            if preferences.preferred_types and activity.type in preferences.preferred_types:
                filtered.append(activity)
            elif not preferences.preferred_types:
                filtered.append(activity)
        
        return filtered[:4]
from app.planner.strategies.base import WeatherStrategy
from app.db.models import Activity, UserPreferences, ActivityType
from typing import List

class SnowyWeatherStrategy(WeatherStrategy):
    async def get_activities(self, user_preferences: UserPreferences) -> List[Activity]:
        activities = [
            Activity(name="Skiing", type=ActivityType.SPORT, priority=5, description="Winter sports fun"),
            Activity(name="Building Snowman", type=ActivityType.OUTDOOR, priority=4, description="Classic winter activity"),
            Activity(name="Hot Chocolate by Fire", type=ActivityType.RELAXATION, priority=4, description="Cozy relaxation"),
            Activity(name="Winter Photography", type=ActivityType.OUTDOOR, priority=3, description="Capture snowy scenes"),
            Activity(name="Baking", type=ActivityType.INDOOR, priority=3, description="Warm up with baking"),
            Activity(name="Reading", type=ActivityType.LEARNING, priority=2, description="Educational reading"),
            Activity(name="Movie Day", type=ActivityType.RELAXATION, priority=3, description="Winter movie marathon")
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
from app.planner.strategies.base import WeatherStrategy
from app.db.models import Activity, UserPreferences, ActivityType
from typing import List

class CloudyWeatherStrategy(WeatherStrategy):
    async def get_activities(self, user_preferences: UserPreferences) -> List[Activity]:
        activities = [
            Activity(name="Museum Visit", type=ActivityType.INDOOR, priority=4, description="Cultural exploration"),
            Activity(name="Shopping", type=ActivityType.INDOOR, priority=3, description="Retail therapy"),
            Activity(name="Light Walking", type=ActivityType.OUTDOOR, priority=3, description="Gentle outdoor activity"),
            Activity(name="Coffee with Friends", type=ActivityType.RELAXATION, priority=3, description="Social time"),
            Activity(name="Studying", type=ActivityType.LEARNING, priority=3, description="Educational activities"),
            Activity(name="Yoga", type=ActivityType.SPORT, priority=2, description="Mindful exercise"),
            Activity(name="House Organization", type=ActivityType.INDOOR, priority=2, description="Declutter your space")
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
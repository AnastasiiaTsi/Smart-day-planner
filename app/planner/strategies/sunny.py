from app.planner.strategies.base import WeatherStrategy
from app.db.models import Activity, UserPreferences, ActivityType
from typing import List

class SunnyWeatherStrategy(WeatherStrategy):
    async def get_activities(self, user_preferences: UserPreferences) -> List[Activity]:
        activities = [
            Activity(name="Hiking", type=ActivityType.OUTDOOR, priority=5, description="Enjoy the sunny weather outdoors"),
            Activity(name="Cycling", type=ActivityType.SPORT, priority=4, description="Great day for a bike ride"),
            Activity(name="Picnic", type=ActivityType.OUTDOOR, priority=3, description="Outdoor dining experience"),
            Activity(name="Gardening", type=ActivityType.OUTDOOR, priority=3, description="Tend to your garden"),
            Activity(name="Beach Visit", type=ActivityType.OUTDOOR, priority=4, description="Relax at the beach"),
            Activity(name="Reading Outside", type=ActivityType.RELAXATION, priority=2, description="Read a book in the sun"),
            Activity(name="Studying", type=ActivityType.LEARNING, priority=2, description="Catch up on studies"),
            Activity(name="House Cleaning", type=ActivityType.INDOOR, priority=1, description="Basic household chores")
        ]
        
        return self._filter_activities(activities, user_preferences)
    
    def _filter_activities(self, activities: List[Activity], preferences: UserPreferences) -> List[Activity]:
        filtered = []
        
        for activity in activities:
            # Skip avoided types
            if activity.type in preferences.avoid_types:
                continue
                
            # Prioritize preferred types
            if preferences.preferred_types and activity.type in preferences.preferred_types:
                filtered.append(activity)
            elif not preferences.preferred_types:
                filtered.append(activity)
        
        return filtered[:4]  # Return top 4 activities
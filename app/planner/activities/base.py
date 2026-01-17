from abc import ABC, abstractmethod
from typing import List
from app.db.models import Activity, UserPreferences

class WeatherStrategy(ABC):
    """Base class for all weather strategies"""
    
    @abstractmethod
    async def get_activities(self, user_preferences: UserPreferences) -> List[Activity]:
        """
        Get activities based on weather and user preferences
        
        Args:
            user_preferences: User's activity preferences
            
        Returns:
            List of recommended activities
        """
        pass
    
    def _filter_activities(self, activities: List[Activity], preferences: UserPreferences) -> List[Activity]:
        """
        Filter activities based on user preferences
        
        Args:
            activities: List of all possible activities
            preferences: User's preferences
            
        Returns:
            Filtered list of activities
        """
        filtered = []
        
        for activity in activities:
            # Skip avoided activity types
            if activity.type in preferences.avoid_types:
                continue
                
            # Prioritize preferred types
            if preferences.preferred_types:
                if activity.type in preferences.preferred_types:
                    filtered.append(activity)
            else:
                # If no preferences specified, include all non-avoided activities
                filtered.append(activity)
        
        # Return top activities (max 4)
        return filtered[:4]
import pytest
import asyncio
from app.planner.day_planner import DayPlanner
from app.db.models import UserPreferences, ActivityType
from app.weather.weather_station import WeatherCondition

class TestDayPlanner:
    @pytest.mark.asyncio
    async def test_day_planner_initialization(self):
        """Test DayPlanner initialization"""
        planner = DayPlanner(user_id="test_user")
        assert planner.user_id == "test_user"
        assert planner.current_plan is None

    @pytest.mark.asyncio
    async def test_planner_weather_update(self):
        """Test DayPlanner response to weather updates"""
        planner = DayPlanner()
        
        weather_data = {
            "condition": WeatherCondition.SUNNY,
            "temperature": 25,
            "humidity": 60,
            "description": "clear sky",
            "location": "Berlin"
        }
        
        await planner.update(weather_data)
        assert planner.current_plan is not None
        assert planner.current_plan.location == "Berlin"
        assert len(planner.current_plan.activities) > 0

    @pytest.mark.asyncio
    async def test_planner_preferences_update(self):
        """Test updating user preferences"""
        planner = DayPlanner()
        
        new_prefs = UserPreferences(
            preferred_types=[ActivityType.INDOOR],
            avoid_types=[ActivityType.OUTDOOR],
            working_hours={"start": 10, "end": 18},
            weekend_mode=False
        )
        
        await planner.set_user_preferences(new_prefs)
        assert planner.user_preferences.preferred_types == [ActivityType.INDOOR]
        assert planner.user_preferences.avoid_types == [ActivityType.OUTDOOR]

    @pytest.mark.asyncio
    async def test_planner_different_weather_conditions(self):
        """Test planner with different weather conditions"""
        planner = DayPlanner()
        
        weather_conditions = [
            (WeatherCondition.SUNNY, "Sunny"),
            (WeatherCondition.RAINY, "Rainy"),
            (WeatherCondition.CLOUDY, "Cloudy"),
            (WeatherCondition.SNOWY, "Snowy")
        ]
        
        for condition, condition_name in weather_conditions:
            weather_data = {
                "condition": condition,
                "temperature": 20,
                "humidity": 50,
                "description": f"{condition_name.lower()} weather",
                "location": "Berlin"
            }
            
            await planner.update(weather_data)
            assert planner.current_plan is not None
            assert len(planner.current_plan.activities) > 0
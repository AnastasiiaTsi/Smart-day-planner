import pytest
import asyncio
from app.db.models import UserPreferences, ActivityType

class TestStrategies:
    @pytest.mark.asyncio
    async def test_sunny_strategy(self, sample_user_preferences):
        """Test SunnyWeatherStrategy"""
        from app.planner.strategies.sunny import SunnyWeatherStrategy
        strategy = SunnyWeatherStrategy()
        activities = await strategy.get_activities(sample_user_preferences)
        
        assert len(activities) > 0
        assert all(isinstance(activity.name, str) for activity in activities)
        assert all(activity.priority >= 1 for activity in activities)
        # Should not contain avoided types
        assert all(activity.type != ActivityType.SPORT for activity in activities)

    @pytest.mark.asyncio
    async def test_rainy_strategy(self, sample_user_preferences):
        """Test RainyWeatherStrategy"""
        from app.planner.strategies.rainy import RainyWeatherStrategy
        strategy = RainyWeatherStrategy()
        activities = await strategy.get_activities(sample_user_preferences)
        
        assert len(activities) > 0
        # Rainy strategy should prefer indoor activities
        indoor_activities = [a for a in activities if a.type in [ActivityType.INDOOR, ActivityType.LEARNING]]
        assert len(indoor_activities) > 0

    @pytest.mark.asyncio
    async def test_all_strategies_return_activities(self, all_strategies, sample_user_preferences):
        """Test that all strategies return activities"""
        for strategy in all_strategies:
            activities = await strategy.get_activities(sample_user_preferences)
            assert len(activities) > 0
            assert len(activities) <= 4  # Max 4 activities per strategy

    @pytest.mark.asyncio
    async def test_strategy_with_empty_preferences(self, all_strategies):
        """Test strategies with empty preferences"""
        empty_prefs = UserPreferences()
        for strategy in all_strategies:
            activities = await strategy.get_activities(empty_prefs)
            assert len(activities) > 0
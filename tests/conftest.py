import sys
import os
import pytest
import asyncio

# Додати корінь проекту до Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.db.models import UserPreferences, Activity, ActivityType
from app.planner.strategies.sunny import SunnyWeatherStrategy
from app.planner.strategies.rainy import RainyWeatherStrategy
from app.planner.strategies.cloudy import CloudyWeatherStrategy
from app.planner.strategies.snowy import SnowyWeatherStrategy

@pytest.fixture
def client():
    """Test client for FastAPI"""
    from fastapi.testclient import TestClient
    return TestClient(app)

@pytest.fixture
def sample_user_preferences():
    """Sample user preferences for testing"""
    return UserPreferences(
        preferred_types=[ActivityType.OUTDOOR, ActivityType.LEARNING],
        avoid_types=[ActivityType.SPORT],
        working_hours={"start": 9, "end": 17},
        weekend_mode=True
    )

@pytest.fixture
def sample_activity():
    """Sample activity for testing"""
    return Activity(
        name="Test Activity",
        type=ActivityType.OUTDOOR,
        priority=3,
        description="Test description"
    )

@pytest.fixture
def all_strategies():
    """All weather strategies for testing"""
    return [
        SunnyWeatherStrategy(),
        RainyWeatherStrategy(),
        CloudyWeatherStrategy(),
        SnowyWeatherStrategy()
    ]

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
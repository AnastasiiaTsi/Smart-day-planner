import pytest
from app.db.models import UserPreferences, Activity, ActivityType, DayPlan

class TestModels:
    def test_user_preferences_creation(self, sample_user_preferences):
        """Test UserPreferences model creation"""
        prefs = sample_user_preferences
        assert prefs.preferred_types == [ActivityType.OUTDOOR, ActivityType.LEARNING]
        assert prefs.avoid_types == [ActivityType.SPORT]
        assert prefs.working_hours == {"start": 9, "end": 17}
        assert prefs.weekend_mode is True

    def test_activity_creation(self, sample_activity):
        """Test Activity model creation"""
        activity = sample_activity
        assert activity.name == "Test Activity"
        assert activity.type == ActivityType.OUTDOOR
        assert activity.priority == 3
        assert activity.description == "Test description"

    def test_activity_priority_validation(self):
        """Test Activity priority validation"""
        # Valid priority
        activity = Activity(name="Test", type=ActivityType.OUTDOOR, priority=5)
        assert activity.priority == 5
        
        # Invalid priority should raise error
        with pytest.raises(ValueError):
            Activity(name="Test", type=ActivityType.OUTDOOR, priority=6)

    def test_day_plan_creation(self):
        """Test DayPlan model creation"""
        activities = [
            Activity(name="Hiking", type=ActivityType.OUTDOOR, priority=5),
            Activity(name="Reading", type=ActivityType.LEARNING, priority=3)
        ]
        
        plan = DayPlan(
            date="2024-01-01",
            location="Berlin",
            weather={"condition": "Sunny", "temperature": 25},
            activities=activities,
            user_id="test_user"
        )
        
        assert plan.date == "2024-01-01"
        assert plan.location == "Berlin"
        assert len(plan.activities) == 2
        assert plan.user_id == "test_user"
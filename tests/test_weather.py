import pytest
import asyncio
from app.weather.weather_api import WeatherAPI
from app.weather.weather_station import WeatherStation, WeatherCondition

class TestWeather:
    @pytest.mark.asyncio
    async def test_weather_api_mock_data(self):
        """Test WeatherAPI with mock data"""
        weather_api = WeatherAPI()
        weather_data = await weather_api.get_weather_data("Berlin")
        
        assert weather_data is not None
        assert "weather" in weather_data
        assert "main" in weather_data
        assert "name" in weather_data
        assert weather_data["name"] == "Berlin"

    def test_weather_condition_mapping(self):
        """Test weather condition mapping"""
        weather_api = WeatherAPI()
        
        # Test different weather conditions
        test_cases = [
            (800, WeatherCondition.SUNNY),
            (500, WeatherCondition.RAINY),
            (600, WeatherCondition.SNOWY),
            (801, WeatherCondition.CLOUDY),
            (300, WeatherCondition.RAINY),
            (701, WeatherCondition.CLOUDY)
        ]
        
        for weather_id, expected_condition in test_cases:
            mock_data = {"weather": [{"id": weather_id}]}
            condition = weather_api.map_weather_condition(mock_data)
            assert condition == expected_condition

    @pytest.mark.asyncio
    async def test_weather_station(self):
        """Test WeatherStation observer pattern"""
        station = WeatherStation()
        
        class MockObserver:
            def __init__(self):
                self.updates = []
            
            async def update(self, weather_data):
                self.updates.append(weather_data)
        
        observer = MockObserver()
        station.attach(observer)
        
        test_weather = {
            "condition": WeatherCondition.SUNNY,
            "temperature": 25,
            "description": "clear sky"
        }
        
        await station.set_weather(test_weather, "Berlin")
        assert len(observer.updates) == 1
        assert observer.updates[0] == test_weather
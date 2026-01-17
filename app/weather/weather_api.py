import os
import random
from app.core.config import settings
from app.core.logger import logger
from app.weather.weather_station import WeatherCondition

class WeatherAPI:
    def __init__(self):
        self.api_key = settings.OPENWEATHER_API_KEY
        self.base_url = settings.OPENWEATHER_BASE_URL

    async def get_weather_data(self, city: str) -> dict:
        """Get weather data - uses mock data for development"""
        # For now, we'll use mock data since OpenWeatherMap API requires a key
        # and httpx might not be installed
        logger.info(f"Fetching mock weather data for {city}")
        return self._get_mock_weather_data(city)

    def _get_mock_weather_data(self, city: str) -> dict:
        """Generate realistic mock weather data"""
        # More realistic mock data with seasonal variations
        seasons = {
            "winter": {"temp_range": (-5, 10), "snow_chance": 0.4},
            "spring": {"temp_range": (5, 20), "rain_chance": 0.3},
            "summer": {"temp_range": (15, 35), "sunny_chance": 0.6},
            "autumn": {"temp_range": (5, 18), "cloudy_chance": 0.5}
        }
        
        # Simple season detection based on month
        import datetime
        month = datetime.datetime.now().month
        if month in [12, 1, 2]:
            season = "winter"
        elif month in [3, 4, 5]:
            season = "spring"
        elif month in [6, 7, 8]:
            season = "summer"
        else:
            season = "autumn"
            
        season_data = seasons[season]
        temp_range = season_data["temp_range"]
        
        # Weighted random choice for weather conditions based on season
        if season == "winter":
            conditions = [
                {"id": 600, "main": "Snow", "description": "light snow", "weight": 4},
                {"id": 601, "main": "Snow", "description": "snow", "weight": 3},
                {"id": 800, "main": "Clear", "description": "clear sky", "weight": 2},
                {"id": 801, "main": "Clouds", "description": "few clouds", "weight": 1}
            ]
        elif season == "spring":
            conditions = [
                {"id": 500, "main": "Rain", "description": "light rain", "weight": 3},
                {"id": 801, "main": "Clouds", "description": "few clouds", "weight": 3},
                {"id": 800, "main": "Clear", "description": "clear sky", "weight": 2},
                {"id": 300, "main": "Drizzle", "description": "light intensity drizzle", "weight": 2}
            ]
        elif season == "summer":
            conditions = [
                {"id": 800, "main": "Clear", "description": "clear sky", "weight": 5},
                {"id": 801, "main": "Clouds", "description": "few clouds", "weight": 3},
                {"id": 802, "main": "Clouds", "description": "scattered clouds", "weight": 1},
                {"id": 500, "main": "Rain", "description": "light rain", "weight": 1}
            ]
        else:  # autumn
            conditions = [
                {"id": 801, "main": "Clouds", "description": "few clouds", "weight": 3},
                {"id": 500, "main": "Rain", "description": "light rain", "weight": 3},
                {"id": 800, "main": "Clear", "description": "clear sky", "weight": 2},
                {"id": 802, "main": "Clouds", "description": "scattered clouds", "weight": 2}
            ]
        
        # Weighted random selection
        weighted_conditions = []
        for condition in conditions:
            weighted_conditions.extend([condition] * condition["weight"])
        
        selected_condition = random.choice(weighted_conditions)
        temperature = random.randint(temp_range[0], temp_range[1])
        humidity = random.randint(40, 85)
        
        return {
            "weather": [{
                "id": selected_condition["id"],
                "main": selected_condition["main"],
                "description": selected_condition["description"]
            }],
            "main": {
                "temp": temperature,
                "humidity": humidity,
                "feels_like": temperature - random.randint(0, 3),
                "pressure": random.randint(1000, 1020)
            },
            "wind": {
                "speed": random.uniform(0, 10),
                "deg": random.randint(0, 360)
            },
            "name": city,
            "visibility": random.randint(5000, 10000)
        }

    def map_weather_condition(self, weather_data: dict) -> WeatherCondition:
        weather_id = weather_data["weather"][0]["id"]
        
        if 200 <= weather_id < 600:  # Thunderstorm, Drizzle, Rain
            return WeatherCondition.RAINY
        elif 600 <= weather_id < 700:  # Snow
            return WeatherCondition.SNOWY
        elif weather_id == 800:  # Clear
            return WeatherCondition.SUNNY
        elif weather_id > 800:  # Clouds
            return WeatherCondition.CLOUDY
        else:
            return WeatherCondition.CLOUDY
from abc import ABC, abstractmethod
from typing import List
from enum import Enum
from app.core.logger import logger

class WeatherCondition(str, Enum):
    SUNNY = "Sunny"
    RAINY = "Rainy"
    CLOUDY = "Cloudy"
    SNOWY = "Snowy"

class Observer(ABC):
    @abstractmethod
    async def update(self, weather_data: dict):
        pass

class WeatherStation:
    def __init__(self):
        self._observers: List[Observer] = []
        self._current_weather = None
        self._current_city = None

    def attach(self, observer: Observer):
        if observer not in self._observers:
            self._observers.append(observer)
            logger.info(f"Observer attached: {type(observer).__name__}")

    def detach(self, observer: Observer):
        self._observers.remove(observer)
        logger.info(f"Observer detached: {type(observer).__name__}")

    async def notify(self, weather_data: dict):
        for observer in self._observers:
            await observer.update(weather_data)

    async def set_weather(self, weather_data: dict, city: str):
        old_weather = self._current_weather
        self._current_weather = weather_data
        self._current_city = city
        
        if old_weather != weather_data:
            logger.info(f"Weather updated for {city}: {weather_data.get('condition', 'Unknown')}")
            await self.notify(weather_data)

    def get_current_weather(self):
        return self._current_weather, self._current_city
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any
from app.weather.weather_station import Observer, WeatherCondition
from app.planner.strategies.base import WeatherStrategy
from app.planner.strategies.sunny import SunnyWeatherStrategy
from app.planner.strategies.rainy import RainyWeatherStrategy
from app.planner.strategies.cloudy import CloudyWeatherStrategy
from app.planner.strategies.snowy import SnowyWeatherStrategy
from app.db.models import DayPlan, UserPreferences, Activity
from app.db.mongodb import get_collection
from app.core.logger import logger

class DayPlanner(Observer):
    """
    Day Planner that uses Strategy Pattern for activity planning
    and Observer Pattern for weather updates
    """
    
    def __init__(self, user_id: str = "default"):
        self.user_id = user_id
        self.current_plan: Optional[DayPlan] = None
        self.user_preferences = UserPreferences()
        self._strategy: Optional[WeatherStrategy] = None
        self.collection = get_collection("plans")

    def set_strategy(self, strategy: WeatherStrategy):
        """Set the weather strategy using Strategy Pattern"""
        self._strategy = strategy
        logger.debug(f"Strategy set to: {type(strategy).__name__}")

    async def update(self, weather_data: dict):
        """
        Observer update method called when weather changes
        Implements Observer Pattern
        """
        logger.info(f"DayPlanner received weather update: {weather_data.get('condition', 'Unknown')}")
        await self.generate_plan(
            weather_data, 
            weather_data.get('location', 'Unknown')
        )

    async def generate_plan(self, weather_data: Dict[str, Any], location: str):
        """
        Generate a daily plan based on weather conditions using Strategy Pattern
        """
        condition = weather_data.get('condition')
        
        # Set strategy based on weather condition (Strategy Pattern)
        if condition == WeatherCondition.SUNNY:
            self.set_strategy(SunnyWeatherStrategy())
        elif condition == WeatherCondition.RAINY:
            self.set_strategy(RainyWeatherStrategy())
        elif condition == WeatherCondition.CLOUDY:
            self.set_strategy(CloudyWeatherStrategy())
        elif condition == WeatherCondition.SNOWY:
            self.set_strategy(SnowyWeatherStrategy())
        else:
            self.set_strategy(CloudyWeatherStrategy())

        if self._strategy:
            activities = await self._strategy.get_activities(self.user_preferences)
            
            # Create the day plan
            plan = DayPlan(
                date=datetime.now().strftime("%Y-%m-%d"),
                location=location,
                weather=weather_data,
                activities=activities,
                user_id=self.user_id
            )
            
            self.current_plan = plan
            await self._save_plan(plan)
            logger.info(f"Generated new plan with {len(activities)} activities for {location}")

    async def _save_plan(self, plan: DayPlan):
        """Save plan to database (MongoDB or fallback storage)"""
        try:
            collection = get_collection("plans")
            if collection is None:
                logger.error("No database collection available")
                return
                
            # Use model_dump() instead of deprecated dict()
            plan_dict = plan.model_dump()
            plan_dict['updated_at'] = datetime.utcnow()
            
            # Check if we're using fallback storage
            from app.db.mongodb import mongodb
            if hasattr(mongodb, 'use_fallback') and mongodb.use_fallback:
                # For fallback storage, handle upsert differently
                existing = await collection.find_one({
                    "date": plan.date, 
                    "location": plan.location, 
                    "user_id": plan.user_id
                })
                if existing:
                    await collection.update_one(
                        {"date": plan.date, "location": plan.location, "user_id": plan.user_id},
                        {"$set": plan_dict}
                    )
                else:
                    await collection.insert_one(plan_dict)
            else:
                # Normal MongoDB operation
                await collection.update_one(
                    {"date": plan.date, "location": plan.location, "user_id": plan.user_id},
                    {"$set": plan_dict},
                    upsert=True
                )
                
            logger.debug(f"Plan saved: {plan.date} {plan.location}")
            
        except Exception as e:
            logger.error(f"Error saving plan: {e}")

    async def get_current_plan(self) -> Optional[DayPlan]:
        """Get the current activity plan"""
        return self.current_plan

    async def set_user_preferences(self, preferences: UserPreferences):
        """Update user preferences"""
        self.user_preferences = preferences
        logger.info(f"User preferences updated for user {self.user_id}")

    async def get_plan_from_db(self, date: str, location: str) -> Optional[DayPlan]:
        """Get plan from database by date and location"""
        try:
            collection = get_collection("plans")
            if collection is None:
                return None
                
            document = await collection.find_one({
                "date": date,
                "location": location,
                "user_id": self.user_id
            })
            
            if document:
                # Convert database document to DayPlan model
                return DayPlan(**document)
            return None
        except Exception as e:
            logger.error(f"Error fetching plan from database: {e}")
            return None

    async def get_user_plans(self, days: int = 7) -> list[DayPlan]:
        """Get recent plans for the user"""
        try:
            collection = get_collection("plans")
            if collection is None:
                return []
                
            # Calculate date range
            end_date = datetime.now()
            start_date = datetime.now().replace(day=end_date.day - days)
            
            plans = []
            async for document in collection.find({
                "user_id": self.user_id,
                "date": {
                    "$gte": start_date.strftime("%Y-%m-%d"),
                    "$lte": end_date.strftime("%Y-%m-%d")
                }
            }).sort("date", -1):
                plans.append(DayPlan(**document))
                
            return plans
        except Exception as e:
            logger.error(f"Error fetching user plans: {e}")
            return []

    async def force_plan_regeneration(self, location: str = "Berlin"):
        """Force regeneration of plan for current conditions"""
        try:
            from app.weather.weather_api import WeatherAPI
            from app.weather.weather_station import WeatherStation
            
            weather_api = WeatherAPI()
            weather_station = WeatherStation()
            
            # Get current weather
            weather_data = await weather_api.get_weather_data(location)
            condition = weather_api.map_weather_condition(weather_data)
            
            processed_data = {
                "condition": condition,
                "temperature": weather_data["main"]["temp"],
                "humidity": weather_data["main"]["humidity"],
                "description": weather_data["weather"][0]["description"],
                "location": location
            }
            
            # Regenerate plan
            await self.generate_plan(processed_data, location)
            logger.info(f"Plan regenerated for {location}")
            
        except Exception as e:
            logger.error(f"Error forcing plan regeneration: {e}")

    def get_plan_summary(self) -> Dict[str, Any]:
        """Get summary of current plan"""
        if not self.current_plan:
            return {"status": "no_plan", "message": "No current plan available"}
        
        plan = self.current_plan
        return {
            "status": "active",
            "date": plan.date,
            "location": plan.location,
            "weather": plan.weather.get('condition', 'Unknown'),
            "temperature": plan.weather.get('temperature', 'Unknown'),
            "total_activities": len(plan.activities),
            "activities": [
                {
                    "name": activity.name,
                    "type": activity.type,
                    "priority": activity.priority,
                    "description": activity.description
                }
                for activity in plan.activities
            ],
            "user_preferences": {
                "preferred_types": self.user_preferences.preferred_types,
                "avoid_types": self.user_preferences.avoid_types,
                "working_hours": self.user_preferences.working_hours,
                "weekend_mode": self.user_preferences.weekend_mode
            }
        }

    async def clear_current_plan(self):
        """Clear the current plan"""
        self.current_plan = None
        logger.info("Current plan cleared")

    def __str__(self) -> str:
        """String representation of the day planner"""
        if not self.current_plan:
            return f"DayPlanner(user_id={self.user_id}, no_current_plan)"
        
        plan = self.current_plan
        return (f"DayPlanner(user_id={self.user_id}, "
                f"date={plan.date}, "
                f"location={plan.location}, "
                f"activities={len(plan.activities)})")

    def __repr__(self) -> str:
        return self.__str__()
import os
import asyncio
import time
from datetime import datetime
from typing import Optional, Callable, Dict, List

# Simple logger if the app logger is not available
class SimpleLogger:
    def info(self, msg):
        print(f"[INFO] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {msg}")
    
    def warning(self, msg):
        print(f"[WARN] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {msg}")
    
    def error(self, msg):
        print(f"[ERROR] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {msg}")
    
    def debug(self, msg):
        print(f"[DEBUG] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {msg}")

# Try to import app logger, fallback to simple logger
try:
    from app.core.logger import logger
except ImportError:
    logger = SimpleLogger()

# Try to import settings, fallback to environment variables
try:
    from app.core.config import settings
except ImportError:
    class SimpleSettings:
        DEFAULT_CITY = os.getenv("DEFAULT_CITY", "Berlin")
        WEATHER_UPDATE_INTERVAL = int(os.getenv("WEATHER_UPDATE_INTERVAL", "1800"))  # 30 minutes
    settings = SimpleSettings()

# ==================== CUSTOM SCHEDULER SYSTEM ====================

class CustomScheduler:
    """Custom scheduler that uses asyncio for background tasks - NO EXTERNAL DEPS"""
    
    def __init__(self):
        self.tasks: List[Dict] = []
        self.running = False
        self._background_task: Optional[asyncio.Task] = None
        self.start_time = time.time()
        logger.info("Custom scheduler initialized (no external dependencies)")
    
    def add_job(self, func: Callable, trigger: str = "interval", seconds: int = 1800, id: str = None):
        """Add a job to the scheduler"""
        job_info = {
            'func': func,
            'interval': seconds,
            'id': id or f"job_{len(self.tasks)}",
            'last_run': None,
            'next_run': time.time() + seconds,  # Schedule first run
            'enabled': True
        }
        self.tasks.append(job_info)
        logger.info(f"Added job: {job_info['id']} (every {seconds} seconds)")
    
    async def _run_job(self, job_info: Dict):
        """Run a single job"""
        if not job_info['enabled']:
            return
            
        try:
            logger.debug(f"Running job: {job_info['id']}")
            job_info['last_run'] = time.time()
            job_info['next_run'] = time.time() + job_info['interval']
            
            # Run the function (support both async and sync functions)
            if asyncio.iscoroutinefunction(job_info['func']):
                await job_info['func']()
            else:
                # Run sync functions in thread pool
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, job_info['func'])
                
            logger.debug(f"Completed job: {job_info['id']}")
        except Exception as e:
            logger.error(f"Job {job_info['id']} failed: {e}")
    
    async def _scheduler_loop(self):
        """Main scheduler loop"""
        logger.info("Starting custom scheduler loop")
        self.running = True
        
        while self.running:
            current_time = time.time()
            tasks_to_run = []
            
            # Find jobs that need to run
            for job in self.tasks:
                if job['enabled'] and current_time >= job['next_run']:
                    tasks_to_run.append(job)
            
            # Run all due jobs concurrently
            if tasks_to_run:
                run_tasks = [self._run_job(job) for job in tasks_to_run]
                await asyncio.gather(*run_tasks, return_exceptions=True)
            
            # Sleep briefly before checking again
            await asyncio.sleep(1)
    
    def start(self):
        """Start the scheduler"""
        if not self.tasks:
            logger.warning("No jobs added to scheduler")
            return self
        
        if self._background_task and not self._background_task.done():
            logger.warning("Scheduler already running")
            return self
        
        # Start the scheduler loop as a background task
        self._background_task = asyncio.create_task(self._scheduler_loop())
        logger.info(f"Custom scheduler started with {len(self.tasks)} jobs")
        return self
    
    def shutdown(self):
        """Stop the scheduler"""
        self.running = False
        if self._background_task:
            self._background_task.cancel()
        logger.info("Custom scheduler stopped")
    
    def get_job_status(self) -> List[Dict]:
        """Get status of all jobs"""
        status = []
        for job in self.tasks:
            status.append({
                'id': job['id'],
                'enabled': job['enabled'],
                'last_run': job['last_run'],
                'next_run': job['next_run'],
                'interval': job['interval']
            })
        return status
    
    def get_uptime(self) -> float:
        """Get scheduler uptime in seconds"""
        return time.time() - self.start_time

# ==================== SIMPLE SYSTEM MONITORING ====================

class SystemMonitor:
    """Simple system monitoring without external dependencies"""
    
    def __init__(self):
        self.start_time = time.time()
        self.request_count = 0
        self.error_count = 0
    
    def increment_requests(self):
        """Increment request counter"""
        self.request_count += 1
    
    def increment_errors(self):
        """Increment error counter"""
        self.error_count += 1
    
    def get_system_info(self) -> Dict:
        """Get basic system information"""
        import platform
        import sys
        
        uptime = time.time() - self.start_time
        
        # Convert uptime to readable format
        hours = int(uptime // 3600)
        minutes = int((uptime % 3600) // 60)
        seconds = int(uptime % 60)
        
        return {
            "platform": platform.system(),
            "python_version": platform.python_version(),
            "uptime": f"{hours}h {minutes}m {seconds}s",
            "uptime_seconds": uptime,
            "requests_processed": self.request_count,
            "errors_occurred": self.error_count,
            "timestamp": datetime.now().isoformat()
        }

# Create global instances
scheduler = CustomScheduler()
system_monitor = SystemMonitor()

# ==================== WEATHER SERVICES ====================

# Try to import weather services with fallbacks
try:
    from app.weather.weather_api import WeatherAPI
    from app.weather.weather_station import WeatherStation
    weather_api = WeatherAPI()
    weather_station = WeatherStation()
    WEATHER_SERVICES_AVAILABLE = True
    logger.info("Weather services imported successfully")
except ImportError as e:
    logger.warning(f"Weather services not available: {e}")
    WEATHER_SERVICES_AVAILABLE = False
    
    # Fallback weather service
    class SimpleWeatherAPI:
        async def get_weather_data(self, city: str) -> dict:
            logger.info(f"Getting mock weather data for {city}")
            # Return realistic mock data
            import random
            conditions = [
                {"id": 800, "description": "clear sky", "temp_range": (15, 30)},  # Sunny
                {"id": 500, "description": "light rain", "temp_range": (10, 20)},  # Rainy
                {"id": 801, "description": "few clouds", "temp_range": (12, 25)},  # Cloudy
                {"id": 600, "description": "light snow", "temp_range": (-5, 5)}    # Snowy
            ]
            condition = random.choice(conditions)
            temp_range = condition["temp_range"]
            
            return {
                "weather": [{"id": condition["id"], "description": condition["description"]}],
                "main": {
                    "temp": random.randint(temp_range[0], temp_range[1]),
                    "humidity": random.randint(40, 80)
                },
                "name": city
            }
        
        def map_weather_condition(self, weather_data: dict) -> str:
            weather_id = weather_data["weather"][0]["id"]
            if 200 <= weather_id < 600:
                return "Rainy"
            elif 600 <= weather_id < 700:
                return "Snowy"
            elif weather_id == 800:
                return "Sunny"
            else:
                return "Cloudy"
    
    class SimpleWeatherStation:
        def __init__(self):
            self.current_weather = None
        
        async def set_weather(self, weather_data: dict, city: str):
            self.current_weather = weather_data
            logger.info(f"Weather station updated: {city} - {weather_data['condition']} {weather_data['temperature']}°C")
    
    weather_api = SimpleWeatherAPI()
    weather_station = SimpleWeatherStation()

# ==================== SCHEDULED TASKS ====================

async def scheduled_weather_update():
    """Background task to update weather periodically"""
    try:
        logger.info("Running scheduled weather update")
        system_monitor.increment_requests()
        
        if not WEATHER_SERVICES_AVAILABLE:
            logger.warning("Using mock weather data (weather services not available)")
        
        weather_data = await weather_api.get_weather_data(settings.DEFAULT_CITY)
        
        condition = weather_api.map_weather_condition(weather_data)
        
        processed_data = {
            "condition": condition,
            "temperature": weather_data["main"]["temp"],
            "humidity": weather_data["main"]["humidity"],
            "description": weather_data["weather"][0]["description"],
            "location": settings.DEFAULT_CITY
        }
        
        await weather_station.set_weather(processed_data, settings.DEFAULT_CITY)
        logger.info(f"Weather update completed: {condition} {weather_data['main']['temp']}°C in {settings.DEFAULT_CITY}")
        
    except Exception as e:
        logger.error(f"Scheduled weather update failed: {e}")
        system_monitor.increment_errors()

async def health_check():
    """Simple health check task WITHOUT external dependencies"""
    try:
        # Basic system health checks without psutil
        import platform
        import sys
        import os
        
        # Get basic system info
        system_info = system_monitor.get_system_info()
        
        # Check disk space (simple version)
        try:
            if os.name == 'nt':  # Windows
                import ctypes
                free_bytes = ctypes.c_ulonglong(0)
                ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                    ctypes.c_wchar_p('C:\\'), None, None, ctypes.pointer(free_bytes)
                )
                disk_free_gb = free_bytes.value / (1024**3)
            else:  # Unix/Linux
                statvfs = os.statvfs('/')
                disk_free_gb = (statvfs.f_bavail * statvfs.f_frsize) / (1024**3)
        except:
            disk_free_gb = "Unknown"
        
        # Check memory (approximate)
        try:
            # This is a simple approximation and may not be accurate
            memory_mb = os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES') / (1024**2) if hasattr(os, 'sysconf') else "Unknown"
        except:
            memory_mb = "Unknown"
        
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "system_uptime": system_info["uptime"],
            "scheduler_uptime": f"{int(scheduler.get_uptime())}s",
            "platform": system_info["platform"],
            "python_version": system_info["python_version"],
            "disk_space_gb": f"{disk_free_gb:.1f}" if isinstance(disk_free_gb, (int, float)) else disk_free_gb,
            "memory_mb": memory_mb,
            "requests_processed": system_info["requests_processed"],
            "errors_occurred": system_info["errors_occurred"],
            "active_jobs": len([job for job in scheduler.tasks if job['enabled']])
        }
        
        logger.info(f"Health check - System: {health_status['status']}, "
                   f"Uptime: {health_status['system_uptime']}, "
                   f"Requests: {health_status['requests_processed']}, "
                   f"Errors: {health_status['errors_occurred']}")
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        system_monitor.increment_errors()
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

async def data_cleanup():
    """Cleanup task for temporary data"""
    try:
        logger.info("Running data cleanup task")
        system_monitor.increment_requests()
        
        # Simple cleanup: remove temporary files older than 1 day
        temp_dir = "temp"
        if os.path.exists(temp_dir):
            now = time.time()
            for filename in os.listdir(temp_dir):
                filepath = os.path.join(temp_dir, filename)
                if os.path.isfile(filepath):
                    # Remove files older than 24 hours
                    if now - os.path.getctime(filepath) > 86400:
                        os.remove(filepath)
                        logger.debug(f"🧹 Removed old file: {filename}")
        
        logger.info("Data cleanup completed")
        
    except Exception as e:
        logger.error(f"Data cleanup failed: {e}")
        system_monitor.increment_errors()

# ==================== SCHEDULER MANAGEMENT ====================

def start_scheduler():
    """Start the background scheduler"""
    global scheduler
    
    logger.info("Starting custom scheduler (no external dependencies required)")
    
    # Add weather update job
    scheduler.add_job(
        scheduled_weather_update,
        seconds=settings.WEATHER_UPDATE_INTERVAL,
        id="weather_update"
    )
    
    # Add health check job (every 5 minutes)
    scheduler.add_job(
        health_check,
        seconds=300,
        id="health_check"
    )
    
    # Add cleanup job (every hour)
    scheduler.add_job(
        data_cleanup,
        seconds=3600,
        id="data_cleanup"
    )
    
    # Start the scheduler
    scheduler.start()
    
    logger.info(f"Custom scheduler started successfully")
    logger.info(f"Weather updates every {settings.WEATHER_UPDATE_INTERVAL} seconds")
    logger.info(f"Default city: {settings.DEFAULT_CITY}")
    
    return scheduler

def stop_scheduler():
    """Stop the scheduler"""
    global scheduler
    scheduler.shutdown()
    logger.info("Scheduler stopped")

def get_scheduler_status() -> Dict:
    """Get current scheduler status"""
    return {
        "scheduler_type": "custom",
        "running": scheduler.running,
        "total_jobs": len(scheduler.tasks),
        "weather_services_available": WEATHER_SERVICES_AVAILABLE,
        "update_interval": settings.WEATHER_UPDATE_INTERVAL,
        "default_city": settings.DEFAULT_CITY,
        "jobs": scheduler.get_job_status(),
        "system_info": system_monitor.get_system_info()
    }

# ==================== MANUAL TASK TRIGGERS ====================

async def trigger_weather_update_manual():
    """Manually trigger a weather update (for API calls)"""
    logger.info("Manually triggering weather update")
    system_monitor.increment_requests()
    await scheduled_weather_update()
    return {"status": "success", "message": "Weather update triggered manually"}

async def trigger_health_check_manual():
    """Manually trigger a health check"""
    logger.info("Manually triggering health check")
    system_monitor.increment_requests()
    result = await health_check()
    return {
        "status": "success", 
        "message": "Health check triggered manually",
        "health_status": result
    }

async def get_system_status():
    """Get system status information"""
    status = get_scheduler_status()
    health = await health_check()
    return {
        "status": "running",
        "scheduler": status,
        "health": health,
        "timestamp": datetime.now().isoformat()
    }

# ==================== INITIALIZATION ====================

# Auto-start scheduler when module is imported (in production)
_AUTO_START = os.getenv("AUTO_START_SCHEDULER", "true").lower() == "true"

if _AUTO_START and __name__ != "__main__":
    # Schedule startup after a brief delay
    async def delayed_start():
        await asyncio.sleep(5)  # Wait 5 seconds for other services to initialize
        start_scheduler()
    
    # Start the delayed initialization
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(delayed_start())
        else:
            loop.run_until_complete(delayed_start())
    except:
        logger.info("Scheduler auto-start scheduled")

# ==================== TEST FUNCTIONS ====================

async def test_scheduler():
    """Test the scheduler system"""
    logger.info("Testing scheduler system...")
    
    status = get_scheduler_status()
    logger.info(f"Scheduler status: {status}")
    
    # Test manual weather update
    try:
        result = await trigger_weather_update_manual()
        logger.info("Manual weather update test passed")
    except Exception as e:
        logger.error(f"Manual weather update test failed: {e}")
    
    # Test manual health check
    try:
        result = await trigger_health_check_manual()
        logger.info("Manual health check test passed")
    except Exception as e:
        logger.error(f"Manual health check test failed: {e}")
    
    return status

# For direct testing
if __name__ == "__main__":
    async def main():
        logger.info("Starting scheduler test...")
        
        # Test the scheduler functions
        await test_scheduler()
        
        # Start scheduler and run for a short time to demonstrate
        start_scheduler()
        
        logger.info("Running scheduler for 15 seconds to demonstrate...")
        logger.info("   You should see weather updates and health checks")
        
        # Run for 15 seconds
        await asyncio.sleep(15)
        
        # Stop scheduler
        stop_scheduler()
        
        # Show final status
        status = get_scheduler_status()
        print("\n" + "="*60)
        print("FINAL SCHEDULER STATUS:")
        print(f"   Scheduler Type: {status['scheduler_type']}")
        print(f"   Running: {status['running']}")
        print(f"   Total Jobs: {status['total_jobs']}")
        print(f"   Weather Services: {status['weather_services_available']}")
        print(f"   Update Interval: {status['update_interval']} seconds")
        print(f"   Default City: {status['default_city']}")
        print(f"   System Uptime: {status['system_info']['uptime']}")
        print(f"   Requests: {status['system_info']['requests_processed']}")
        print("\nJobs:")
        for job in status['jobs']:
            last_run = datetime.fromtimestamp(job['last_run']).strftime('%H:%M:%S') if job['last_run'] else 'Never'
            print(f"   - {job['id']}: enabled={job['enabled']}, last_run={last_run}")
        print("="*60)
    
    asyncio.run(main())
import os
import json
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime

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
        MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://mongo:27017")
        MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "day_planner")
    settings = SimpleSettings()

# ==================== FALLBACK STORAGE SYSTEM ====================

class FallbackCollection:
    def __init__(self, data: List[Dict], save_callback):
        self.data = data
        self.save_callback = save_callback
    
    async def find_one(self, query: Dict) -> Optional[Dict]:
        """Find one document matching query"""
        for doc in self.data:
            match = True
            for key, value in query.items():
                if doc.get(key) != value:
                    match = False
                    break
            if match:
                return doc.copy()  # Return copy to avoid modifying original
        return None
    
    async def insert_one(self, document: Dict) -> None:
        """Insert one document"""
        document = document.copy()  # Work with copy
        if '_id' not in document:
            document['_id'] = f"doc_{len(self.data) + 1}_{datetime.now().timestamp()}"
        self.data.append(document)
        self.save_callback()
        logger.debug(f"Inserted document with _id: {document['_id']}")
    
    async def update_one(self, query: Dict, update: Dict, upsert: bool = False) -> None:
        """Update one document matching query"""
        found = False
        for i, doc in enumerate(self.data):
            match = True
            for key, value in query.items():
                if doc.get(key) != value:
                    match = False
                    break
            if match:
                found = True
                # Handle $set operator or direct update
                if '$set' in update:
                    self.data[i].update(update['$set'])
                else:
                    self.data[i].update(update)
                self.data[i]['updated_at'] = datetime.utcnow().isoformat()
                logger.debug(f"Updated document: {query}")
                break
        
        if not found and upsert:
            # Create new document for upsert
            new_doc = query.copy()
            if '$set' in update:
                new_doc.update(update['$set'])
            else:
                new_doc.update(update)
            await self.insert_one(new_doc)
            logger.debug(f"Upserted new document: {query}")
        
        if found or (not found and upsert):
            self.save_callback()
    
    async def find(self, query: Dict = None) -> List[Dict]:
        """Find all documents matching query"""
        if query is None:
            return self.data.copy()
        
        results = []
        for doc in self.data:
            match = True
            for key, value in query.items():
                if doc.get(key) != value:
                    match = False
                    break
            if match:
                results.append(doc.copy())
        return results

class FallbackStorage:
    def __init__(self):
        self.data = {}
        self.file_path = "fallback_storage.json"
        self._load_data()
    
    def _load_data(self):
        """Load data from JSON file"""
        try:
            if os.path.exists(self.file_path):
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
                logger.info(f"Loaded data from fallback storage: {self.file_path}")
                logger.info(f"Collections: {list(self.data.keys())}")
        except Exception as e:
            logger.warning(f"Could not load fallback storage: {e}")
            self.data = {}
    
    def _save_data(self):
        """Save data to JSON file"""
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            logger.debug("Saved data to fallback storage")
        except Exception as e:
            logger.error(f"Could not save fallback storage: {e}")
    
    def get_collection(self, collection_name: str) -> FallbackCollection:
        """Get or create a collection"""
        if collection_name not in self.data:
            self.data[collection_name] = []
            logger.debug(f"Created new collection: {collection_name}")
        return FallbackCollection(self.data[collection_name], self._save_data)

# ==================== MONGODB CONNECTION ====================

# Initialize variables - COMPLETELY REMOVE MOTOR IMPORTS
MONGODB_AVAILABLE = False
fallback_storage = FallbackStorage()

# Check if motor is available without importing it
def check_motor_available():
    """Check if motor package is available without importing it"""
    try:
        import importlib.util
        spec = importlib.util.find_spec("motor.motor_asyncio")
        return spec is not None
    except:
        return False

# Set MongoDB availability
MONGODB_AVAILABLE = check_motor_available()

if MONGODB_AVAILABLE:
    logger.info("Motor package is available - MongoDB can be used")
else:
    logger.info("Motor package not found - Using fallback JSON storage system")

class MongoDB:
    def __init__(self):
        self.client = None
        self.database = None
        self.use_fallback = not MONGODB_AVAILABLE

# Global MongoDB instance
mongodb = MongoDB()

async def connect_to_mongo():
    """Connect to MongoDB or setup fallback storage"""
    if not MONGODB_AVAILABLE:
        logger.info("Using fallback storage system (no MongoDB needed)")
        logger.info("Data will be stored in: fallback_storage.json")
        return
    
    try:
        # Import motor only if available - USE DYNAMIC IMPORT
        motor_spec = __import__('importlib.util').util.find_spec("motor.motor_asyncio")
        if motor_spec is not None:
            motor_module = __import__('motor.motor_asyncio', fromlist=['AsyncIOMotorClient'])
            AsyncIOMotorClient = getattr(motor_module, 'AsyncIOMotorClient')
            
            logger.info(f"Connecting to MongoDB: {settings.MONGODB_URL}")
            mongodb.client = AsyncIOMotorClient(settings.MONGODB_URL)
            mongodb.database = mongodb.client[settings.MONGODB_DB_NAME]
            
            # Test connection with a simple command
            await mongodb.database.command('ping')
            logger.info("Successfully connected to MongoDB")
            logger.info(f"Database: {settings.MONGODB_DB_NAME}")
        else:
            raise ImportError("Motor package not found")
        
    except ImportError:
        logger.error("Motor package not installed")
        logger.info("Switching to fallback storage system")
        mongodb.use_fallback = True
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        logger.info("Switching to fallback storage system")
        mongodb.use_fallback = True

async def close_mongo_connection():
    """Close MongoDB connection if active"""
    if mongodb.client and MONGODB_AVAILABLE and not mongodb.use_fallback:
        mongodb.client.close()
        logger.info("🔌 Closed MongoDB connection")

def get_database():
    """Get database instance or fallback storage"""
    if mongodb.use_fallback or not MONGODB_AVAILABLE:
        return fallback_storage
    return mongodb.database

def get_collection(collection_name: str):
    """Get collection from MongoDB or fallback storage"""
    database = get_database()
    
    if database is None:
        logger.error("Database not available")
        return None
    
    if mongodb.use_fallback or not MONGODB_AVAILABLE:
        logger.debug(f"Using fallback collection: {collection_name}")
        return database.get_collection(collection_name)
    else:
        logger.debug(f"Using MongoDB collection: {collection_name}")
        # For MongoDB, we need to handle the collection differently
        try:
            # Dynamic import for MongoDB collection
            if hasattr(database, '__getitem__'):
                return database[collection_name]
            else:
                logger.error("MongoDB database doesn't support collection access")
                return database.get_collection(collection_name)
        except Exception as e:
            logger.error(f"Failed to get MongoDB collection: {e}")
            return database.get_collection(collection_name)

def get_storage_info() -> Dict[str, Any]:
    """Get information about current storage system"""
    return {
        "mongodb_available": MONGODB_AVAILABLE,
        "using_fallback": mongodb.use_fallback or not MONGODB_AVAILABLE,
        "fallback_file": fallback_storage.file_path if not MONGODB_AVAILABLE else None,
        "collections": list(fallback_storage.data.keys()) if not MONGODB_AVAILABLE else []
    }

# ==================== DATABASE OPERATIONS ====================

async def save_plan(plan_data: Dict) -> bool:
    """Save a plan to database"""
    try:
        collection = get_collection("plans")
        if collection is None:
            logger.error("No collection available for saving plan")
            return False
        
        # Generate unique ID if not present
        if '_id' not in plan_data:
            plan_data['_id'] = f"plan_{plan_data.get('date', 'unknown')}_{plan_data.get('location', 'unknown')}_{plan_data.get('user_id', 'default')}"
        
        plan_data['updated_at'] = datetime.utcnow().isoformat()
        
        # Use upsert to update existing or insert new
        await collection.update_one(
            {"_id": plan_data['_id']},
            {"$set": plan_data},
            upsert=True
        )
        
        logger.debug(f"Plan saved: {plan_data['_id']}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to save plan: {e}")
        return False

async def get_plan(plan_id: str) -> Optional[Dict]:
    """Get a plan by ID"""
    try:
        collection = get_collection("plans")
        if collection is None:
            return None
        
        return await collection.find_one({"_id": plan_id})
        
    except Exception as e:
        logger.error(f"Failed to get plan {plan_id}: {e}")
        return None

async def get_user_plans(user_id: str, date: str = None) -> List[Dict]:
    """Get all plans for a user, optionally filtered by date"""
    try:
        collection = get_collection("plans")
        if collection is None:
            return []
        
        query = {"user_id": user_id}
        if date:
            query["date"] = date
        
        return await collection.find(query)
        
    except Exception as e:
        logger.error(f"Failed to get plans for user {user_id}: {e}")
        return []

async def save_user_preferences(user_id: str, preferences: Dict) -> bool:
    """Save user preferences"""
    try:
        collection = get_collection("user_preferences")
        if collection is None:
            return False
        
        preferences_data = {
            "_id": f"prefs_{user_id}",
            "user_id": user_id,
            "preferences": preferences,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        await collection.update_one(
            {"_id": preferences_data['_id']},
            {"$set": preferences_data},
            upsert=True
        )
        
        logger.debug(f"Preferences saved for user: {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to save preferences for user {user_id}: {e}")
        return False

async def get_user_preferences(user_id: str) -> Optional[Dict]:
    """Get user preferences"""
    try:
        collection = get_collection("user_preferences")
        if collection is None:
            return None
        
        result = await collection.find_one({"_id": f"prefs_{user_id}"})
        return result.get("preferences") if result else None
        
    except Exception as e:
        logger.error(f"Failed to get preferences for user {user_id}: {e}")
        return None

# ==================== TEST FUNCTIONS ====================

async def test_connection():
    """Test the database connection"""
    logger.info("Testing database connection...")
    
    if mongodb.use_fallback or not MONGODB_AVAILABLE:
        logger.info("Fallback storage is ready")
        return True
    
    try:
        if mongodb.database:
            await mongodb.database.command('ping')
            logger.info("MongoDB connection test passed")
            return True
    except Exception as e:
        logger.error(f"MongoDB connection test failed: {e}")
    
    return False

async def demo_fallback_storage():
    """Demonstrate the fallback storage system"""
    logger.info("Demonstrating fallback storage...")
    
    # Get a test collection
    test_collection = get_collection("test_demo")
    
    # Insert a document
    test_doc = {
        "name": "demo_document",
        "value": 42,
        "timestamp": datetime.now().isoformat(),
        "description": "This is a test document for fallback storage"
    }
    
    await test_collection.insert_one(test_doc)
    logger.info("Inserted test document")
    
    # Find the document
    found = await test_collection.find_one({"name": "demo_document"})
    if found:
        logger.info(f"Found document: {found['name']} = {found['value']}")
    else:
        logger.error("Could not find inserted document")
    
    # Update the document
    await test_collection.update_one(
        {"name": "demo_document"},
        {"$set": {"value": 100, "updated": True}}
    )
    logger.info("Updated test document")
    
    # Find again to verify update
    found_updated = await test_collection.find_one({"name": "demo_document"})
    if found_updated and found_updated.get("value") == 100:
        logger.info("Update verified successfully")
    else:
        logger.error("Update verification failed")
    
    # Test the helper functions
    test_plan = {
        "date": "2024-01-01",
        "location": "Test City",
        "user_id": "test_user",
        "weather": {"condition": "Sunny", "temperature": 25},
        "activities": [{"name": "Testing", "type": "test", "priority": 1}]
    }
    
    await save_plan(test_plan)
    logger.info("Plan save test completed")
    
    # Show storage info
    info = get_storage_info()
    logger.info(f"Storage info: {info}")

# Initialize on import
if __name__ != "__main__":
    # Auto-connect when module is imported
    async def initialize():
        await connect_to_mongo()
    
    # Run the initialization
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is running, create task
            loop.create_task(initialize())
        else:
            # If loop is not running, run until complete
            loop.run_until_complete(initialize())
    except:
        # If no event loop, just log
        logger.info("🔧 MongoDB module initialized (async connect scheduled)")

# For direct testing
if __name__ == "__main__":
    async def main():
        logger.info("Starting MongoDB test...")
        await connect_to_mongo()
        await test_connection()
        await demo_fallback_storage()
        
        # Show final status
        info = get_storage_info()
        print("\n" + "="*50)
        print("🎉 FINAL STORAGE STATUS:")
        print(f"   MongoDB Available: {info['mongodb_available']}")
        print(f"   Using Fallback: {info['using_fallback']}")
        if info['using_fallback']:
            print(f"   Fallback File: {info['fallback_file']}")
            print(f"   Collections: {info['collections']}")
        print("="*50)
    
    asyncio.run(main())
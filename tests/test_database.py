import pytest
import asyncio
from app.db.mongodb import connect_to_mongo, get_collection, save_plan, get_plan
from app.db.models import Activity, ActivityType

class TestDatabase:
    @pytest.mark.asyncio
    async def test_database_connection(self):
        """Test database connection (will use fallback if MongoDB not available)"""
        await connect_to_mongo()

    @pytest.mark.asyncio
    async def test_fallback_storage(self):
        """Test fallback storage operations"""
    
        test_plan = {
            "date": "2024-01-01",
            "location": "Test City",
            "user_id": "test_user",
            "weather": {"condition": "Sunny", "temperature": 25},
            "activities": [
                {"name": "Testing", "type": "indoor", "priority": 1}
            ]
        }
        
        result = await save_plan(test_plan)
        assert result is True
        
        plan_id = "plan_2024-01-01_Test City_test_user"
        retrieved_plan = await get_plan(plan_id)
        assert retrieved_plan is not None
        assert retrieved_plan["location"] == "Test City"

    @pytest.mark.asyncio
    async def test_collection_operations(self):
        """Test collection operations with fallback"""
        collection = get_collection("test_collection")
        assert collection is not None
        
        test_doc = {"name": "test_document", "value": 42}
        await collection.insert_one(test_doc)
        
        found_doc = await collection.find_one({"name": "test_document"})
        assert found_doc is not None
        assert found_doc["value"] == 42  
        
        test_doc2 = {"name": "test_document_2", "value": 50}
        await collection.insert_one(test_doc2)
        
        await collection.update_one(
            {"name": "test_document_2"},
            {"$set": {"value": 100}}
        )
        
        updated_doc = await collection.find_one({"name": "test_document_2"})
        assert updated_doc is not None
        assert updated_doc["value"] == 100 
        

        original_doc = await collection.find_one({"name": "test_document"})
        assert original_doc is not None
        assert original_doc["value"] == 42 
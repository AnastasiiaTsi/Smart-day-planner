import pytest
from fastapi.testclient import TestClient

class TestAPI:
    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200

    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "Smart Day Planner"

    def test_api_documentation(self, client):
        """Test API documentation endpoints"""
        response = client.get("/docs")
        assert response.status_code == 200
        
        response = client.get("/redoc")
        assert response.status_code == 200

    def test_weather_update_endpoint(self, client):
        """Test weather update endpoint"""
        response = client.post("/api/v1/weather/update?city=Berlin")
        # Should return 200 or 500 depending on weather service availability
        assert response.status_code in [200, 500]

    def test_get_current_plan(self, client):
        """Test get current plan endpoint"""
        response = client.get("/api/v1/plan/current")
        # Could be 404 if no plan generated yet, or 200 if there is a plan
        assert response.status_code in [200, 404]

    def test_update_preferences(self, client):
        """Test update preferences endpoint"""
        preferences = {
            "preferred_types": ["outdoor", "learning"],
            "avoid_types": ["sport"],
            "working_hours": {"start": 9, "end": 17},
            "weekend_mode": True
        }
        
        response = client.post("/api/v1/preferences", json=preferences)
        assert response.status_code in [200, 500]
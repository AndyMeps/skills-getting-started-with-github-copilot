"""
Tests for the Mergington High School API
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path to import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def reset_activities(client):
    """Reset the activities to initial state before each test by reloading the app"""
    # Reload the app module to reset the in-memory database
    import importlib
    import app as app_module
    importlib.reload(app_module)
    
    # Create a fresh client with the reloaded app
    fresh_client = TestClient(app_module.app)
    yield fresh_client


class TestGetActivities:
    """Test cases for GET /activities endpoint"""
    
    def test_get_activities_returns_dict(self, client):
        """Test that /activities endpoint returns a dictionary"""
        response = client.get("/activities")
        assert response.status_code == 200
        assert isinstance(response.json(), dict)
    
    def test_get_activities_contains_expected_activities(self, client):
        """Test that /activities contains expected activity names"""
        response = client.get("/activities")
        activities = response.json()
        
        expected_activities = [
            "Basketball",
            "Tennis Club",
            "Art Studio",
            "Drama Club",
            "Debate Team",
            "Robotics Club",
            "Chess Club",
            "Programming Class",
            "Gym Class"
        ]
        
        for activity in expected_activities:
            assert activity in activities
    
    def test_activity_has_required_fields(self, client):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        activities = response.json()
        
        for activity_name, activity_data in activities.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)


class TestSignup:
    """Test cases for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_for_existing_activity(self, reset_activities):
        """Test signing up for an existing activity"""
        response = reset_activities.post(
            "/activities/Basketball/signup",
            params={"email": "test@mergington.edu"}
        )
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]
    
    def test_signup_adds_participant(self, reset_activities):
        """Test that signup adds the email to participants"""
        email = "test@mergington.edu"
        
        # Sign up
        reset_activities.post(
            "/activities/Basketball/signup",
            params={"email": email}
        )
        
        # Verify signup was added
        response = reset_activities.get("/activities")
        activities = response.json()
        assert email in activities["Basketball"]["participants"]
    
    def test_signup_for_nonexistent_activity(self, reset_activities):
        """Test signing up for an activity that doesn't exist"""
        response = reset_activities.post(
            "/activities/NonexistentActivity/signup",
            params={"email": "test@mergington.edu"}
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_signup_duplicate_email(self, reset_activities):
        """Test that signing up twice with same email fails"""
        email = "test@mergington.edu"
        activity = "Basketball"
        
        # First signup should succeed
        response1 = reset_activities.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Second signup with same email should fail
        response2 = reset_activities.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response2.status_code == 400
        assert "already signed up" in response2.json()["detail"]


class TestUnregister:
    """Test cases for DELETE /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_from_activity(self, reset_activities):
        """Test unregistering from an activity"""
        email = "test@mergington.edu"
        activity = "Basketball"
        
        # First sign up
        reset_activities.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        # Then unregister
        response = reset_activities.delete(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]
    
    def test_unregister_removes_participant(self, reset_activities):
        """Test that unregister removes the email from participants"""
        email = "test@mergington.edu"
        activity = "Basketball"
        
        # Sign up
        reset_activities.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        # Unregister
        reset_activities.delete(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        
        # Verify removal
        response = reset_activities.get("/activities")
        activities = response.json()
        assert email not in activities[activity]["participants"]
    
    def test_unregister_from_nonexistent_activity(self, reset_activities):
        """Test unregistering from an activity that doesn't exist"""
        response = reset_activities.delete(
            "/activities/NonexistentActivity/unregister",
            params={"email": "test@mergington.edu"}
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_unregister_when_not_signed_up(self, reset_activities):
        """Test unregistering when not signed up for the activity"""
        response = reset_activities.delete(
            "/activities/Basketball/unregister",
            params={"email": "nosignup@mergington.edu"}
        )
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]


class TestRoot:
    """Test cases for the root endpoint"""
    
    def test_root_redirects_to_static(self, client):
        """Test that root endpoint redirects to static files"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code in [301, 302, 307, 308]
        assert "/static" in response.headers.get("location", "")

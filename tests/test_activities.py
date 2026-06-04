"""
Tests for Mergington High School Activities API endpoints.
"""
import pytest


class TestGetActivities:
    """Tests for GET /activities endpoint."""

    def test_get_activities_returns_all_activities(self, client, fresh_activities):
        """Test that GET /activities returns all activities with correct structure."""
        response = client.get("/activities")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify all three activities are present
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
        
        # Verify each activity has required fields
        for activity_name, activity_details in data.items():
            assert "description" in activity_details
            assert "schedule" in activity_details
            assert "max_participants" in activity_details
            assert "participants" in activity_details
            assert isinstance(activity_details["participants"], list)

    def test_get_activities_returns_correct_participant_count(self, client, fresh_activities):
        """Test that participant counts are accurate."""
        response = client.get("/activities")
        data = response.json()
        
        assert len(data["Chess Club"]["participants"]) == 2
        assert len(data["Programming Class"]["participants"]) == 2
        assert len(data["Gym Class"]["participants"]) == 2

    def test_get_activities_structure_details(self, client, fresh_activities):
        """Test that activity details have correct values."""
        response = client.get("/activities")
        data = response.json()
        
        chess = data["Chess Club"]
        assert chess["description"] == "Learn strategies and compete in chess tournaments"
        assert chess["schedule"] == "Fridays, 3:30 PM - 5:00 PM"
        assert chess["max_participants"] == 12
        assert "michael@mergington.edu" in chess["participants"]
        assert "daniel@mergington.edu" in chess["participants"]


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint."""

    def test_signup_valid_activity_and_email(self, client, fresh_activities):
        """Test successful signup for an activity."""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "alice@mergington.edu"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "alice@mergington.edu" in data["message"]
        assert "Chess Club" in data["message"]
        
        # Verify participant was added
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert "alice@mergington.edu" in activities["Chess Club"]["participants"]

    def test_signup_invalid_activity_returns_404(self, client, fresh_activities):
        """Test signup fails with 404 for non-existent activity."""
        response = client.post(
            "/activities/Nonexistent Club/signup",
            params={"email": "alice@mergington.edu"}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    def test_signup_multiple_students_same_activity(self, client, fresh_activities):
        """Test multiple different students can sign up for same activity."""
        # Sign up first student
        response1 = client.post(
            "/activities/Chess Club/signup",
            params={"email": "alice@mergington.edu"}
        )
        assert response1.status_code == 200
        
        # Sign up second student
        response2 = client.post(
            "/activities/Chess Club/signup",
            params={"email": "bob@mergington.edu"}
        )
        assert response2.status_code == 200
        
        # Verify both are in participants
        activities_response = client.get("/activities")
        activities = activities_response.json()
        participants = activities["Chess Club"]["participants"]
        assert "alice@mergington.edu" in participants
        assert "bob@mergington.edu" in participants

    def test_signup_duplicate_email_allowed(self, client, fresh_activities):
        """Test that duplicate signup is allowed (no duplicate check in current implementation)."""
        # Sign up same student twice
        response1 = client.post(
            "/activities/Chess Club/signup",
            params={"email": "alice@mergington.edu"}
        )
        assert response1.status_code == 200
        
        # Note: Current implementation allows duplicates
        # This test documents current behavior; validation could be added later
        response2 = client.post(
            "/activities/Chess Club/signup",
            params={"email": "alice@mergington.edu"}
        )
        assert response2.status_code == 200

    def test_signup_different_activities(self, client, fresh_activities):
        """Test a student can sign up for multiple different activities."""
        # Sign up for Chess Club
        response1 = client.post(
            "/activities/Chess Club/signup",
            params={"email": "charlie@mergington.edu"}
        )
        assert response1.status_code == 200
        
        # Sign up for Programming Class
        response2 = client.post(
            "/activities/Programming Class/signup",
            params={"email": "charlie@mergington.edu"}
        )
        assert response2.status_code == 200
        
        # Verify in both activities
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert "charlie@mergington.edu" in activities["Chess Club"]["participants"]
        assert "charlie@mergington.edu" in activities["Programming Class"]["participants"]

    def test_signup_empty_email_allowed(self, client, fresh_activities):
        """Test signup with empty email (no validation in current implementation)."""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": ""}
        )
        # Current implementation accepts empty strings
        assert response.status_code == 200


class TestRemoveParticipant:
    """Tests for DELETE /activities/{activity_name}/participants endpoint."""

    def test_remove_existing_participant_success(self, client, fresh_activities):
        """Test successful removal of a participant from an activity."""
        response = client.delete(
            "/activities/Chess Club/participants",
            params={"email": "michael@mergington.edu"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "michael@mergington.edu" in data["message"]
        
        # Verify participant was removed
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert "michael@mergington.edu" not in activities["Chess Club"]["participants"]
        # Other participant should still be there
        assert "daniel@mergington.edu" in activities["Chess Club"]["participants"]

    def test_remove_from_invalid_activity_returns_404(self, client, fresh_activities):
        """Test removal fails with 404 for non-existent activity."""
        response = client.delete(
            "/activities/Nonexistent Club/participants",
            params={"email": "alice@mergington.edu"}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    def test_remove_nonexistent_participant_returns_404(self, client, fresh_activities):
        """Test removal fails with 404 when participant not found."""
        response = client.delete(
            "/activities/Chess Club/participants",
            params={"email": "nonexistent@mergington.edu"}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    def test_remove_all_participants_from_activity(self, client, fresh_activities):
        """Test removing all participants from an activity."""
        # Remove first participant
        response1 = client.delete(
            "/activities/Chess Club/participants",
            params={"email": "michael@mergington.edu"}
        )
        assert response1.status_code == 200
        
        # Remove second participant
        response2 = client.delete(
            "/activities/Chess Club/participants",
            params={"email": "daniel@mergington.edu"}
        )
        assert response2.status_code == 200
        
        # Verify activity now has no participants
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert len(activities["Chess Club"]["participants"]) == 0

    def test_remove_participant_from_different_activities_independent(self, client, fresh_activities):
        """Test that removing from one activity doesn't affect others."""
        # Remove from Chess Club
        response1 = client.delete(
            "/activities/Chess Club/participants",
            params={"email": "michael@mergington.edu"}
        )
        assert response1.status_code == 200
        
        # Verify removed from Chess Club
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert "michael@mergington.edu" not in activities["Chess Club"]["participants"]
        
        # Verify not affected in other activities (michael is only in Chess)
        # This is a sanity check for current data
        assert "michael@mergington.edu" not in activities["Programming Class"]["participants"]
        assert "michael@mergington.edu" not in activities["Gym Class"]["participants"]


class TestIntegrationWorkflows:
    """Integration tests combining multiple endpoints."""

    def test_signup_then_remove_workflow(self, client, fresh_activities):
        """Test signing up then removing a participant."""
        # Sign up
        signup_response = client.post(
            "/activities/Programming Class/signup",
            params={"email": "dave@mergington.edu"}
        )
        assert signup_response.status_code == 200
        
        # Verify signed up
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert "dave@mergington.edu" in activities["Programming Class"]["participants"]
        
        # Remove
        remove_response = client.delete(
            "/activities/Programming Class/participants",
            params={"email": "dave@mergington.edu"}
        )
        assert remove_response.status_code == 200
        
        # Verify removed
        final_activities = client.get("/activities").json()
        assert "dave@mergington.edu" not in final_activities["Programming Class"]["participants"]

    def test_signup_multiple_then_remove_one(self, client, fresh_activities):
        """Test signing up multiple participants then removing one."""
        # Sign up three students
        for i, email in enumerate(["user1@mergington.edu", "user2@mergington.edu", "user3@mergington.edu"]):
            response = client.post(
                "/activities/Gym Class/signup",
                params={"email": email}
            )
            assert response.status_code == 200
        
        # Verify all three signed up
        activities = client.get("/activities").json()
        gym_participants = activities["Gym Class"]["participants"]
        assert "user1@mergington.edu" in gym_participants
        assert "user2@mergington.edu" in gym_participants
        assert "user3@mergington.edu" in gym_participants
        
        # Remove one
        remove_response = client.delete(
            "/activities/Gym Class/participants",
            params={"email": "user2@mergington.edu"}
        )
        assert remove_response.status_code == 200
        
        # Verify only one removed
        final_activities = client.get("/activities").json()
        final_participants = final_activities["Gym Class"]["participants"]
        assert "user1@mergington.edu" in final_participants
        assert "user2@mergington.edu" not in final_participants
        assert "user3@mergington.edu" in final_participants

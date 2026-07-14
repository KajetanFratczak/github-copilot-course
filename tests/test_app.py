import copy
from urllib.parse import quote

import pytest
from httpx import AsyncClient, ASGITransport

from src.app import app, activities


@pytest.fixture(autouse=True)
def reset_activities():
    original_activities = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(copy.deepcopy(original_activities))


@pytest.mark.asyncio
async def test_get_activities_returns_activity_data():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/activities")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "Chess Club" in data
    assert data["Chess Club"]["description"] == "Learn strategies and compete in chess tournaments"
    assert data["Chess Club"]["participants"] == ["michael@mergington.edu", "daniel@mergington.edu"]


@pytest.mark.asyncio
async def test_signup_adds_participant():
    email = "newstudent@mergington.edu"
    activity_name = "Chess Club"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(f"/activities/{quote(activity_name)}/signup?email={quote(email)}")

        assert response.status_code == 200
        assert response.json()["message"] == f"Signed up {email} for {activity_name}"

        response = await client.get("/activities")
        assert email in response.json()[activity_name]["participants"]


@pytest.mark.asyncio
async def test_duplicate_signup_returns_400():
    email = "michael@mergington.edu"
    activity_name = "Chess Club"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(f"/activities/{quote(activity_name)}/signup?email={quote(email)}")

        assert response.status_code == 400
        assert response.json()["detail"] == "Student already signed up for this activity"


@pytest.mark.asyncio
async def test_delete_participant_removes_participant():
    email = "daniel@mergington.edu"
    activity_name = "Chess Club"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.delete(f"/activities/{quote(activity_name)}/participants?email={quote(email)}")

        assert response.status_code == 200
        assert response.json()["message"] == f"Removed {email} from {activity_name}"

        response = await client.get("/activities")
        assert email not in response.json()[activity_name]["participants"]


@pytest.mark.asyncio
async def test_delete_missing_participant_returns_404():
    email = "missing@mergington.edu"
    activity_name = "Chess Club"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.delete(f"/activities/{quote(activity_name)}/participants?email={quote(email)}")

        assert response.status_code == 404
        assert response.json()["detail"] == "Participant not found"

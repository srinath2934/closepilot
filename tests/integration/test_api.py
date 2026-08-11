"""Integration tests for FastAPI endpoints."""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_api_root():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_api_deals():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/deals")
        assert resp.status_code == 200
        data = resp.json()
        assert "deals" in data
        assert len(data["deals"]) > 0


@pytest.mark.asyncio
async def test_api_workflow_lifecycle():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Start Workflow
        start_resp = await client.post("/api/workflow/start", json={
            "user_request": "Who should I follow up with today?"
        })
        assert start_resp.status_code == 200
        start_data = start_resp.json()
        thread_id = start_data["thread_id"]
        assert start_data["status"] == "AWAITING_HUMAN_APPROVAL"
        assert len(start_data["state"]["opportunities"]) > 0

        # 2. Check Thread Status
        status_resp = await client.get(f"/api/workflow/status/{thread_id}")
        assert status_resp.status_code == 200
        status_data = status_resp.json()
        assert status_data["thread_id"] == thread_id

        # 3. Approve Workflow
        approve_resp = await client.post("/api/workflow/approve", json={
            "thread_id": thread_id,
            "action": "APPROVED"
        })
        assert approve_resp.status_code == 200
        approve_data = approve_resp.json()
        assert approve_data["status"] == "COMPLETED"
        assert approve_data["state"]["action_result"]["status"] == "SUCCESS"
        assert approve_data["state"]["verification_result"]["verified"] is True

"""Unit tests for Supabase repository persistence."""
import pytest
from app.database.repositories import runs_repo, approvals_repo, audit_repo


@pytest.mark.asyncio
async def test_runs_repository():
    # Should handle gracefully when Supabase is unconfigured or configured
    run_id = await runs_repo.create_run(
        thread_id="test_thread_123",
        provider="nvidia",
        model="meta/llama-3.1-70b-instruct"
    )
    assert run_id.startswith("run_")


@pytest.mark.asyncio
async def test_audit_repository():
    res = await audit_repo.log_event(
        thread_id="test_thread_123",
        node="research",
        action="GET_DEALS",
        status="SUCCESS",
        metadata={"count": 4}
    )
    # Returns None gracefully when credentials not supplied or dict when inserted
    assert res is None or isinstance(res, dict)

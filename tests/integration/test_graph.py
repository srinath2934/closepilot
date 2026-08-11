"""Integration tests for LangGraph sales workflow and HITL execution."""
import pytest
import uuid
from app.graph.graph import create_sales_graph
from langgraph.checkpoint.memory import MemorySaver


@pytest.mark.asyncio
async def test_end_to_end_graph_execution():
    checkpointer = MemorySaver()
    graph = create_sales_graph(checkpointer)
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    initial_state = {
        "user_request": "Who should I follow up with today?",
        "intent": "FIND_FOLLOWUPS",
        "deals": [],
        "contacts": [],
        "activities": [],
        "opportunities": [],
        "selected_opportunity": None,
        "priority_score": None,
        "strategy": None,
        "followup_draft": None,
        "approval_status": None,
        "action_result": None,
        "verification_result": None,
        "errors": [],
        "retry_count": 0
    }

    # Step 1: Execute graph until interrupt before approval
    result_step1 = await graph.ainvoke(initial_state, config=config)

    assert len(result_step1["opportunities"]) > 0
    assert result_step1["selected_opportunity"] is not None
    assert result_step1["strategy"] is not None
    assert result_step1["followup_draft"] is not None
    assert result_step1["action_result"] is None  # Must NOT write before approval

    # Step 2: Update state with human approval and resume execution
    await graph.aupdate_state(config, {"approval_status": "APPROVED"}, as_node="communication")
    result_step2 = await graph.ainvoke(None, config=config)

    assert result_step2["action_result"] is not None
    assert result_step2["action_result"]["status"] == "SUCCESS"
    assert result_step2["verification_result"] is not None
    assert result_step2["verification_result"]["verified"] is True

"""Comprehensive Multi-Scenario Integration Test Suite for GWC AI Sales Agent."""
import pytest
import uuid
from app.graph.graph import create_sales_graph
from langgraph.checkpoint.memory import MemorySaver


@pytest.mark.asyncio
async def test_scenario_1_standard_flow():
    """Scenario 1: Standard prioritization and approval."""
    checkpointer = MemorySaver()
    graph = create_sales_graph(checkpointer)
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    initial_state = {
        "thread_id": thread_id,
        "user_request": "Who should I follow up with today?",
        "intent": "FIND_FOLLOWUPS",
        "deals": [], "contacts": [], "activities": [],
        "opportunities": [], "selected_opportunity": None,
        "priority_score": None, "strategy": None,
        "followup_draft": None, "approval_status": None,
        "action_result": None, "verification_result": None,
        "errors": [], "retry_count": 0
    }

    step1 = await graph.ainvoke(initial_state, config=config)
    assert step1["selected_opportunity"] is not None
    assert step1["strategy"] is not None
    assert step1["followup_draft"] is not None

    await graph.aupdate_state(config, {"approval_status": "APPROVED"}, as_node="communication")
    step2 = await graph.ainvoke(None, config=config)
    assert step2["action_result"]["status"] == "SUCCESS"
    assert step2["verification_result"]["verified"] is True


@pytest.mark.asyncio
async def test_scenario_2_custom_prompt_targeting():
    """Scenario 2: Custom prompt dynamically boosts targeted deal."""
    checkpointer = MemorySaver()
    graph = create_sales_graph(checkpointer)
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    custom_request = "Follow up with Sarah at NexaCloud regarding SLA terms"
    initial_state = {
        "thread_id": thread_id,
        "user_request": custom_request,
        "intent": "FIND_FOLLOWUPS",
        "deals": [], "contacts": [], "activities": [],
        "opportunities": [], "selected_opportunity": None,
        "priority_score": None, "strategy": None,
        "followup_draft": None, "approval_status": None,
        "action_result": None, "verification_result": None,
        "errors": [], "retry_count": 0
    }

    result = await graph.ainvoke(initial_state, config=config)
    top_deal = result["selected_opportunity"]
    assert "NexaCloud" in top_deal["name"]
    assert any("custom prompt query" in r for r in top_deal["score_reasons"])


@pytest.mark.asyncio
async def test_scenario_3_deal_switching_synchronization():
    """Scenario 3: Opportunity Switcher correctly updates checkpointer for action execution."""
    checkpointer = MemorySaver()
    graph = create_sales_graph(checkpointer)
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    initial_state = {
        "thread_id": thread_id,
        "user_request": "Who should I follow up with today?",
        "intent": "FIND_FOLLOWUPS",
        "deals": [], "contacts": [], "activities": [],
        "opportunities": [], "selected_opportunity": None,
        "priority_score": None, "strategy": None,
        "followup_draft": None, "approval_status": None,
        "action_result": None, "verification_result": None,
        "errors": [], "retry_count": 0
    }

    step1 = await graph.ainvoke(initial_state, config=config)
    opps = step1["opportunities"]
    assert len(opps) >= 2

    # Switch to the 2nd opportunity
    second_opp = opps[1]
    await graph.aupdate_state(
        config,
        {
            "selected_opportunity": second_opp,
            "priority_score": second_opp.get("score"),
            "approval_status": "APPROVED"
        },
        as_node="communication"
    )

    step2 = await graph.ainvoke(None, config=config)
    assert step2["action_result"]["deal_id"] == second_opp["id"]


@pytest.mark.asyncio
async def test_scenario_4_rejection_safety():
    """Scenario 4: Rejection halts write action."""
    checkpointer = MemorySaver()
    graph = create_sales_graph(checkpointer)
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    initial_state = {
        "thread_id": thread_id,
        "user_request": "Who should I follow up with today?",
        "intent": "FIND_FOLLOWUPS",
        "deals": [], "contacts": [], "activities": [],
        "opportunities": [], "selected_opportunity": None,
        "priority_score": None, "strategy": None,
        "followup_draft": None, "approval_status": None,
        "action_result": None, "verification_result": None,
        "errors": [], "retry_count": 0
    }

    await graph.ainvoke(initial_state, config=config)
    await graph.aupdate_state(config, {"approval_status": "REJECTED"}, as_node="communication")
    step2 = await graph.ainvoke(None, config=config)
    assert step2["action_result"]["status"] == "SKIPPED"


@pytest.mark.asyncio
async def test_scenario_5_human_draft_modification():
    """Scenario 5: User-modified subject and body are preserved in action execution."""
    checkpointer = MemorySaver()
    graph = create_sales_graph(checkpointer)
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    initial_state = {
        "thread_id": thread_id,
        "user_request": "Who should I follow up with today?",
        "intent": "FIND_FOLLOWUPS",
        "deals": [], "contacts": [], "activities": [],
        "opportunities": [], "selected_opportunity": None,
        "priority_score": None, "strategy": None,
        "followup_draft": None, "approval_status": None,
        "action_result": None, "verification_result": None,
        "errors": [], "retry_count": 0
    }

    await graph.ainvoke(initial_state, config=config)
    custom_subject = "Special Executive Offer - Q3 Exclusive"
    custom_body = "Hello, here is a custom tailored proposal approved by leadership."

    await graph.aupdate_state(
        config,
        {
            "approval_status": "APPROVED",
            "followup_draft": {
                "subject": custom_subject,
                "body": custom_body,
                "action_type": "CREATE_CRM_TASK_AND_DRAFT_EMAIL"
            }
        },
        as_node="communication"
    )

    step2 = await graph.ainvoke(None, config=config)
    assert step2["action_result"]["status"] == "SUCCESS"
    assert step2["followup_draft"]["subject"] == custom_subject

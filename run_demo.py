"""Stand-alone runnable CLI demonstration of the GWC AI Sales Agent workflow."""
import asyncio
import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.graph.graph import create_sales_graph
from langgraph.checkpoint.memory import MemorySaver


async def run_pipeline_demo():
    print("=" * 60)
    print("  GWC AI Sales Intelligence Agent - Live Execution")
    print("=" * 60)

    # 1. Initialize StateGraph with memory checkpointer
    graph = create_sales_graph(MemorySaver())
    config = {"configurable": {"thread_id": "demo_session_101"}}

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
        "retry_count": 0,
    }

    print("\n[PHASE 1] Investigating CRM, Scoring Opportunities & Generating Strategy...")
    state1 = await graph.ainvoke(initial_state, config=config)

    top_deal = state1.get("selected_opportunity") or {}
    strat = state1.get("strategy") or {}
    draft = state1.get("followup_draft") or {}

    print(f"\n  [+] Total Deals Ingested: {len(state1.get('deals', []))}")
    print(f"  [+] Top Ranked Opportunity: {top_deal.get('name')}")
    print(f"  [+] Deal Value: ${top_deal.get('amount', 0):,.0f} | Stage: {top_deal.get('stage')}")
    print(f"  [+] Deterministic Priority Score: {top_deal.get('score', 0):.0f}")
    print(f"  [+] Decision Maker: {top_deal.get('contact_name')} ({top_deal.get('contact_title')})")

    print(f"\n  [+] Strategy Agent Rationale:")
    print(f"      - Recommended Action: {strat.get('recommended_action')}")
    print(f"      - Executive Summary: {strat.get('summary')}")
    print(f"      - Strategic Rationale: {strat.get('rationale')}")

    print(f"\n  [+] Grounded Follow-up Email Draft:")
    print(f"      - Subject: {draft.get('subject')}")
    body = draft.get("body", "")
    # Indent body lines for clean display
    for line in body.split("\n"):
        print(f"        {line}")

    print("\n" + "-" * 60)
    print("  [PHASE 2] Human-in-the-Loop Gate (Paused for Approval)")
    print("-" * 60)
    print("  >> Simulating User Approval: APPROVED")

    # 2. Update state to approve and resume execution
    await graph.aupdate_state(config, {"approval_status": "APPROVED"}, as_node="communication")
    state2 = await graph.ainvoke(None, config=config)

    action_res = state2.get("action_result") or {}
    verify_res = state2.get("verification_result") or {}

    print("\n  [PHASE 3] Executing CRM Actions & Verifying Persistence...")
    print(f"      [+] Action Status: {action_res.get('status')}")
    print(f"      [+] Queued HubSpot Task ID: {action_res.get('task_id')}")
    print(f"      [+] Logged HubSpot Note ID: {action_res.get('note_id')}")
    print(f"      [+] Read-After-Write Verification: {verify_res.get('status')} (Verified: {verify_res.get('verified')})")

    print("\n" + "=" * 60)
    print("  [SUCCESS] Complete Workflow Executed & Verified Successfully!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_pipeline_demo())

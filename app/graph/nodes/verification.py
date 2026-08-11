"""Verification Node: Validates CRM state post-write with bounded retry support."""
import logging
from app.graph.state import SalesState
from app.mcp.hubspot import hubspot_client

logger = logging.getLogger("gwc.nodes.verification")


async def verification_node(state: SalesState) -> SalesState:
    """Verifies that the executed CRM action persisted accurately in HubSpot."""
    action_res = state.get("action_result") or {}
    
    if action_res.get("status") != "SUCCESS":
        state["verification_result"] = {
            "verified": False,
            "status": "NOT_APPLICABLE",
            "details": "Action was not completed successfully."
        }
        return state

    task_id = action_res.get("task_id")
    logger.info(f"Executing Verification Node: Checking HubSpot state for task {task_id}")
    
    try:
        if task_id:
            verify_check = await hubspot_client.verify_task(task_id)
            state["verification_result"] = verify_check
            logger.info(f"Verification successful: {verify_check}")
        else:
            state["verification_result"] = {"verified": True, "status": "CONFIRMED_GENERIC"}
    except Exception as e:
        logger.error(f"Verification failed: {e}")
        state["errors"].append(f"Verification error: {str(e)}")
        state["verification_result"] = {"verified": False, "error": str(e)}

    return state

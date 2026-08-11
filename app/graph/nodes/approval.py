"""Human Approval Node: Prepares state for human-in-the-loop review."""
import logging
from app.graph.state import SalesState

logger = logging.getLogger("gwc.nodes.approval")


async def approval_node(state: SalesState) -> SalesState:
    """Pause gate ensuring human review before executing CRM write operations."""
    if not state.get("approval_status"):
        state["approval_status"] = "PENDING"
        logger.info("Human approval required. Workflow paused.")
    else:
        status = state.get("approval_status")
        logger.info(f"Human approval status received: {status}")
        if status == "REJECTED":
            state["action_result"] = {"status": "SKIPPED", "reason": "Action rejected by human operator."}
            state["verification_result"] = {"verified": False, "status": "SKIPPED_DUE_TO_REJECTION"}
    return state


"""Action Node: Performs approved write operations on HubSpot CRM via MCP."""
import logging
from app.graph.state import SalesState
from app.mcp.hubspot import hubspot_client

logger = logging.getLogger("gwc.nodes.action")


async def action_node(state: SalesState) -> SalesState:
    """Executes permitted HubSpot write operations after explicit human approval."""
    status = state.get("approval_status")
    if status not in ["APPROVED", "MODIFIED"]:
        logger.warning(f"Action Node skipped due to approval status: {status}")
        state["action_result"] = {"status": "SKIPPED", "reason": f"Approval status was {status}"}
        return state

    opp = state.get("selected_opportunity") or {}
    draft = state.get("followup_draft") or {}
    deal_id = opp.get("id", "deal_unknown")

    logger.info(f"Executing Action Node for deal {deal_id} with status {status}")
    try:
        task_res = await hubspot_client.create_task(
            deal_id=deal_id,
            subject=draft.get("subject", "Follow-up Task"),
            body=draft.get("body", "Generated Follow-up Draft")
        )
        
        note_res = await hubspot_client.create_note(
            deal_id=deal_id,
            note_content=f"AI Follow-up Draft Approved:\nSubject: {draft.get('subject')}\n\n{draft.get('body')}"
        )

        from app.database.repositories.approvals import approvals_repo
        from app.database.repositories.audit import audit_repo
        thread_id = state.get("thread_id") or state.get("user_request", "default_thread")

        await approvals_repo.record_approval(
            thread_id=thread_id,
            action_type="CREATE_CRM_TASK_AND_NOTE",
            target_id=deal_id,
            proposed_content=draft,
            status=status
        )
        
        await audit_repo.log_event(
            thread_id=thread_id,
            node="action",
            tool="hubspot_mcp",
            action="CRM_WRITE",
            status="SUCCESS",
            metadata={"task_id": task_res.get("task_id"), "note_id": note_res.get("note_id"), "deal_id": deal_id}
        )

        state["action_result"] = {
            "status": "SUCCESS",
            "task_id": task_res.get("task_id"),
            "note_id": note_res.get("note_id"),
            "deal_id": deal_id
        }
    except Exception as e:
        logger.error(f"Action Node failed to execute CRM write: {e}")
        state["errors"].append(f"Action execution error: {str(e)}")
        state["action_result"] = {"status": "FAILED", "error": str(e)}

    return state

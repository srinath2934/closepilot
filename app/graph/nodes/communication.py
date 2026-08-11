"""Communication Agent Node: Drafts context-grounded follow-up messages."""
import logging
from app.graph.state import SalesState
from app.llm.provider import get_llm_provider
from app.prompts import COMMUNICATION_SYSTEM_PROMPT, format_communication_user_prompt

logger = logging.getLogger("gwc.nodes.communication")


async def communication_node(state: SalesState) -> SalesState:
    """Drafts personalized follow-up email based on verified CRM notes."""
    logger.info("Executing Communication Node: Drafting evidence-grounded follow-up.")
    opp = state.get("selected_opportunity")
    strat = state.get("strategy") or {}

    if not opp:
        state["errors"].append("No opportunity available to draft communication.")
        return state

    user_request = state.get("user_request", "Who should I follow up with today?")
    user_prompt = format_communication_user_prompt(
        contact_name=opp.get("contact_name", "Valued Client"),
        contact_title=opp.get("contact_title", "Decision Maker"),
        company_name=opp.get("company_name", "Enterprise Client"),
        contact_email=opp.get("contact_email", "lead@client.com"),
        deal_name=opp.get("name", "Strategic Partnership"),
        amount=float(opp.get("amount", 0)),
        stage=opp.get("stage", "Qualified"),
        notes=opp.get("notes", []),
        recommended_action=strat.get("recommended_action", "SEND_FOLLOWUP_EMAIL"),
        rationale=strat.get("rationale", "Follow-up based on deal urgency."),
        user_request=user_request
    )

    try:
        llm = get_llm_provider()
        draft_json = await llm.generate_json(COMMUNICATION_SYSTEM_PROMPT, user_prompt)
        state["followup_draft"] = draft_json
    except Exception as e:
        logger.error(f"Communication Agent failed: {e}")
        state["followup_draft"] = {
            "subject": f"Follow-up: {opp.get('name')} Next Steps",
            "body": f"Hi {opp.get('contact_name', 'Valued Client')},\n\nFollowing up on our discussions regarding {opp.get('name')}. Let me know if you have any questions on the proposal.\n\nBest regards,\nSales Team",
            "action_type": "CREATE_CRM_TASK_AND_DRAFT_EMAIL"
        }

    return state

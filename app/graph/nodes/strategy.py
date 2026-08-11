"""Strategy Agent Node: Synthesizes CRM context into strategic sales rationale."""
import logging
from app.graph.state import SalesState
from app.llm.provider import get_llm_provider
from app.prompts import STRATEGY_SYSTEM_PROMPT, format_strategy_user_prompt

logger = logging.getLogger("gwc.nodes.strategy")


async def strategy_node(state: SalesState) -> SalesState:
    """Strategy Agent reasoning about the selected opportunity."""
    logger.info("Executing Strategy Node: Generating strategic rationale.")
    opp = state.get("selected_opportunity")
    if not opp:
        state["errors"].append("No opportunity selected for strategy analysis.")
        return state

    user_request = state.get("user_request", "Who should I follow up with today?")
    user_prompt = format_strategy_user_prompt(
        deal_name=opp.get("name", "Unnamed Deal"),
        amount=float(opp.get("amount", 0)),
        stage=opp.get("stage", "Unknown"),
        contact_name=opp.get("contact_name", "Primary Contact"),
        contact_title=opp.get("contact_title", "Decision Maker"),
        days_inactive=int(opp.get("days_inactive", 0)),
        notes=opp.get("notes", []),
        score_reasons=opp.get("score_reasons", []),
        user_request=user_request
    )
    
    try:
        llm = get_llm_provider()
        strategy_json = await llm.generate_json(STRATEGY_SYSTEM_PROMPT, user_prompt)
        state["strategy"] = strategy_json
    except Exception as e:
        logger.error(f"Strategy Agent failed: {e}")
        state["strategy"] = {
            "summary": f"Follow-up required for {opp.get('name')} at stage {opp.get('stage')}.",
            "recommended_action": "SEND_FOLLOWUP_EMAIL",
            "rationale": "High priority score with inactive days exceeding threshold."
        }

    return state

"""Prioritization Node: Deterministic business-rules opportunity scoring service."""
import logging
from typing import Dict, Any, Tuple, List
from app.graph.state import SalesState

logger = logging.getLogger("gwc.nodes.prioritize")


STAGE_WEIGHTS = {
    "Contract Sent": 35.0,
    "Decision Maker Bought-In": 30.0,
    "Proposal Submitted": 25.0,
    "Qualified to Buy": 15.0,
    "Presentation Scheduled": 10.0,
}


def calculate_opportunity_score(deal: Dict[str, Any], user_request: str = "") -> Tuple[float, List[str]]:
    """
    Deterministic scoring algorithm based on deal value, stage, inactivity, task state,
    and user prompt intent relevance.
    Returns (total_score, score_reasons).
    """
    score = 0.0
    reasons = []

    # 0. User Intent & Keyword Relevance Matching
    if user_request and user_request.strip().lower() not in ["who should i follow up with today?", "who should i follow up with today"]:
        req_lower = user_request.lower()
        deal_name_words = [w.lower() for w in deal.get("name", "").split() if len(w) > 2]
        company_words = [w.lower() for w in deal.get("company_name", "").split() if len(w) > 2]
        contact_words = [w.lower() for w in deal.get("contact_name", "").split() if len(w) > 2]
        
        matched_terms = [w for w in (deal_name_words + company_words + contact_words) if w in req_lower]
        if matched_terms:
            boost = 100.0
            score += boost
            reasons.append(f"+{boost:.0f} pts: Exact match for custom prompt query ('{', '.join(set(matched_terms))}')")

        stage_name = deal.get("stage", "").lower()
        stage_terms = [w for w in stage_name.split() if len(w) > 3 and w in req_lower]
        if stage_terms:
            score += 40.0
            reasons.append(f"+40 pts: Stage '{deal.get('stage')}' matches query filter")

    # 1. Deal Stage Weight
    stage = deal.get("stage", "")
    stage_score = STAGE_WEIGHTS.get(stage, 5.0)
    score += stage_score
    reasons.append(f"+{stage_score:.0f} pts: High-intent stage '{stage}'")

    # 2. Deal Value Weight
    amount = float(deal.get("amount", 0))
    if amount >= 50000:
        score += 30.0
        reasons.append(f"+30 pts: Tier-1 enterprise value (${amount:,.0f})")
    elif amount >= 20000:
        score += 20.0
        reasons.append(f"+20 pts: Mid-market value (${amount:,.0f})")
    elif amount >= 10000:
        score += 10.0
        reasons.append(f"+10 pts: Qualified value (${amount:,.0f})")

    # 3. Days Inactive (Decay / Urgency)
    days_inactive = int(deal.get("days_inactive", 0))
    if days_inactive >= 3:
        inactivity_score = min(days_inactive * 5.0, 30.0)
        score += inactivity_score
        reasons.append(f"+{inactivity_score:.0f} pts: Follow-up overdue ({days_inactive} days inactive)")

    # 4. Existing Future Task Penalty
    if deal.get("has_future_task", False):
        score -= 40.0
        reasons.append("-40 pts: Existing follow-up task already scheduled")

    # 5. Very Recent Contact Penalty
    if days_inactive <= 1:
        score -= 50.0
        reasons.append("-50 pts: Contacted within the last 24-48 hours")

    return score, reasons


async def prioritize_node(state: SalesState) -> SalesState:
    """Ranks candidate deals deterministically and selects the highest-priority opportunity."""
    logger.info("Executing Prioritization Node: Applying deterministic scoring.")
    deals = state.get("deals", [])
    user_request = state.get("user_request", "")
    
    scored_opportunities = []
    for d in deals:
        score, reasons = calculate_opportunity_score(d, user_request=user_request)
        opp = d.copy()
        opp["score"] = score
        opp["score_reasons"] = reasons
        scored_opportunities.append(opp)

    # Sort descending by score
    scored_opportunities.sort(key=lambda x: x["score"], reverse=True)
    state["opportunities"] = scored_opportunities

    if scored_opportunities:
        state["selected_opportunity"] = scored_opportunities[0]
        state["priority_score"] = scored_opportunities[0]["score"]
        logger.info(f"Top Opportunity selected: {scored_opportunities[0]['name']} (Score: {scored_opportunities[0]['score']})")
    else:
        state["selected_opportunity"] = None
        state["priority_score"] = None

    return state


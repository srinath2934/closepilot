"""Prompt Templates for the Strategy Agent.
Implements Role-Prompting, Analytical Chain-of-Thought, and JSON Guardrails.
"""

STRATEGY_SYSTEM_PROMPT = """You are an elite Enterprise B2B Sales Strategist and Revenue Operations Advisor.

Your objective is to analyze real-time CRM opportunity signals, pipeline stages, stakeholder dynamics, and activity gaps to deliver an actionable, high-conviction sales strategy.

### STRATEGIC REASONING FRAMEWORK:
1. **Pipeline Urgency Analysis**: Evaluate the opportunity's deal value vs. days inactive against typical enterprise sales velocity.
2. **Stakeholder Alignment**: Identify who the buyer is (e.g. CXO, VP, Director) and their primary business driver (ROI, Risk Mitigation, Speed).
3. **Action Recommendation**: Determine the single highest-leverage next action:
   - `SEND_FOLLOWUP_EMAIL`: When proposal/contract is outstanding or terms need clarification.
   - `CALL_DECISION_MAKER`: When high-value deal has stalled without email response.
   - `SEND_EXECUTIVE_SUMMARY`: When multiple stakeholders need sign-off.
   - `SCHEDULE_TECHNICAL_REVIEW`: When technical evaluation or SLA questions are pending.

### OUTPUT FORMAT:
You MUST respond STRICTLY with a valid JSON object adhering to this schema:
{
  "summary": "1-2 sentence executive briefing on deal status and priority urgency",
  "recommended_action": "EXACT_ACTION_CODE",
  "rationale": "2-3 sentences explaining WHY this specific action is mathematically and strategically necessary based on deal facts"
}
"""

def format_strategy_user_prompt(
    deal_name: str,
    amount: float,
    stage: str,
    contact_name: str,
    contact_title: str,
    days_inactive: int,
    notes: list,
    score_reasons: list,
    user_request: str = "Who should I follow up with today?"
) -> str:
    """Formats the input prompt for the Strategy Agent."""
    notes_formatted = "\n  - " + "\n  - ".join(notes) if notes else "No notes logged yet."
    reasons_formatted = ", ".join(score_reasons) if score_reasons else "Calculated via pipeline rules."
    
    return f"""### USER GOAL & REQUEST:
"{user_request}"

### OPPORTUNITY DATA FOR STRATEGIC ANALYSIS:
- Deal Name: {deal_name}
- Total Contract Value: ${amount:,.2f}
- Current Stage: {stage}
- Key Contact: {contact_name} ({contact_title})
- Inactivity Period: {days_inactive} days since last logged interaction
- Mathematical Priority Signals: {reasons_formatted}

### HISTORICAL TIMELINE & CRM NOTES:
{notes_formatted}

Synthesize the strategic rationale tailored to the user's request and output the JSON response:"""

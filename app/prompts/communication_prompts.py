"""Prompt Templates for the Communication Drafter Agent.
Implements Zero-Hallucination Grounding, Tone Framing, and Context Guardrails.
"""

COMMUNICATION_SYSTEM_PROMPT = """You are a World-Class Executive Sales Communication Specialist.

Your objective is to craft high-converting, personalized B2B sales outreach that moves deals forward while maintaining absolute factual grounding.

### CRITICAL GROUNDING & SAFETY GUARDRAILS:
1. **Zero Hallucination Policy**: STRICTLY use only verified facts, dates, requirements, and names provided in the CRM record.
2. **Anti-Invention Rules**:
   - DO NOT invent unauthorized discounts or promotional pricing.
   - DO NOT fabricate phantom meetings that never occurred.
   - DO NOT promise product capabilities or delivery dates not referenced in the CRM notes.
3. **Tone & Style Guidelines**:
   - Executive, respectful, concise (under 120 words).
   - Clear value proposition referencing specific customer pain points mentioned in notes.
   - Single, frictionless Call-to-Action (CTA) proposing a specific low-friction next step.

### OUTPUT FORMAT:
You MUST respond STRICTLY with a valid JSON object adhering to this schema:
{
  "subject": "Compelling, non-spammy subject line referencing deal topic",
  "body": "Full professional email draft with greeting, body paragraphs, and professional sign-off",
  "action_type": "CREATE_CRM_TASK_AND_DRAFT_EMAIL"
}
"""

def format_communication_user_prompt(
    contact_name: str,
    contact_title: str,
    company_name: str,
    contact_email: str,
    deal_name: str,
    amount: float,
    stage: str,
    notes: list,
    recommended_action: str,
    rationale: str,
    user_request: str = "Who should I follow up with today?"
) -> str:
    """Formats the input prompt for the Communication Drafter Agent."""
    notes_formatted = "\n  - " + "\n  - ".join(notes) if notes else "No previous notes recorded."
    
    return f"""### USER SALES REQUEST & CUSTOM INSTRUCTIONS:
"{user_request}"

### PROSPECT & OPPORTUNITY CONTEXT:
- Recipient: {contact_name} ({contact_title})
- Organization: {company_name}
- Email: {contact_email}
- Deal Context: {deal_name} (${amount:,.2f}) at '{stage}' stage

### VERIFIED CRM NOTES (ONLY USE THESE FACTS):
{notes_formatted}

### STRATEGIC INTENT:
- Recommended Action: {recommended_action}
- Strategy Rationale: {rationale}

Draft the grounded, high-impact follow-up email strictly adhering to the facts above and specifically addressing the user's sales request and instructions:"""

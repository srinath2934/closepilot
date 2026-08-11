"""LangGraph Shared State Schema for GWC AI Sales Agent."""
from typing import List, Dict, Any, Optional
from typing_extensions import TypedDict


class SalesState(TypedDict):
    # Workflow & Session Identity
    thread_id: Optional[str]

    # Initial input
    user_request: str
    intent: str

    # Retrieved CRM context
    deals: List[Dict[str, Any]]
    contacts: List[Dict[str, Any]]
    activities: List[Dict[str, Any]]

    # Prioritization & Selection
    opportunities: List[Dict[str, Any]]
    selected_opportunity: Optional[Dict[str, Any]]
    priority_score: Optional[float]

    # Reasoning & Generation
    strategy: Optional[Dict[str, Any]]
    followup_draft: Optional[Dict[str, Any]]

    # Human-in-the-Loop Approval
    approval_status: Optional[str]  # "PENDING" | "APPROVED" | "REJECTED" | "MODIFIED"

    # Action & Verification
    action_result: Optional[Dict[str, Any]]
    verification_result: Optional[Dict[str, Any]]

    # Diagnostic & Fault-Tolerance
    errors: List[str]
    retry_count: int

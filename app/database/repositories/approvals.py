"""Repository for recording human approval decisions in Supabase."""
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from app.database.connection import supabase_client


class ApprovalsRepository:
    """Manages human approval audits and history."""
    @staticmethod
    async def record_approval(
        thread_id: str,
        action_type: str,
        target_id: str,
        proposed_content: Dict[str, Any],
        status: str = "APPROVED",
        user_modifications: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        approval_id = f"appr_{uuid.uuid4().hex[:10]}"
        record = {
            "approval_id": approval_id,
            "thread_id": thread_id,
            "action_type": action_type,
            "target_id": target_id,
            "proposed_content": proposed_content,
            "status": status,
            "reviewed_at": datetime.now().isoformat(),
            "user_modifications": user_modifications
        }
        return await supabase_client.insert("approval_requests", record)


approvals_repo = ApprovalsRepository()

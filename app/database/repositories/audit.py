"""Repository for logging workflow audit events in Supabase."""
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from app.database.connection import supabase_client


class AuditRepository:
    """Manages audit trail events for every agent node execution."""
    @staticmethod
    async def log_event(
        thread_id: str,
        node: str,
        action: str,
        status: str = "SUCCESS",
        tool: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        event_id = f"evt_{uuid.uuid4().hex[:10]}"
        record = {
            "event_id": event_id,
            "thread_id": thread_id,
            "node": node,
            "tool": tool,
            "action": action,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata
        }
        return await supabase_client.insert("audit_events", record)


audit_repo = AuditRepository()

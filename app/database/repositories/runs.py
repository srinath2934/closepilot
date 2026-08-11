"""Repository for managing agent thread and run records in Supabase."""
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from app.database.connection import supabase_client


class RunsRepository:
    """Manages thread state and run telemetry."""
    @staticmethod
    async def create_thread(thread_id: str, user_id: str = "sales_rep_1") -> Optional[Dict[str, Any]]:
        record = {
            "thread_id": thread_id,
            "user_id": user_id,
            "status": "ACTIVE",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        return await supabase_client.insert("agent_threads", record)

    @staticmethod
    async def create_run(thread_id: str, provider: str, model: str) -> str:
        run_id = f"run_{uuid.uuid4().hex[:10]}"
        record = {
            "run_id": run_id,
            "thread_id": thread_id,
            "provider": provider,
            "model": model,
            "status": "RUNNING",
            "started_at": datetime.now().isoformat()
        }
        await supabase_client.insert("agent_runs", record)
        return run_id


runs_repo = RunsRepository()

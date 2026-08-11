"""Supabase Database Connection and REST Client."""
import logging
import httpx
from typing import Dict, Any, List, Optional
from app.config.settings import settings

logger = logging.getLogger("gwc.database")


class SupabaseClient:
    """Lightweight async Supabase PostgREST client with circuit-breaker."""
    def __init__(self):
        self._circuit_open = False

    @property
    def url(self) -> Optional[str]:
        return settings.SUPABASE_URL
        
    @property
    def key(self) -> Optional[str]:
        return settings.SUPABASE_KEY
        
    @property
    def enabled(self) -> bool:
        return bool(self.url and self.key and not self._circuit_open)

    def _headers(self) -> Dict[str, str]:
        return {
            "apikey": self.key or "",
            "Authorization": f"Bearer {self.key or ''}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }

    async def insert(self, table: str, record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Insert a single record into a Supabase table."""
        if not self.enabled:
            return None
        endpoint = f"{self.url.rstrip('/')}/rest/v1/{table}"
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                resp = await client.post(endpoint, headers=self._headers(), json=record)
                if resp.status_code == 401:
                    logger.info("Supabase API returned 401 Unauthorized (JWT key needed). Silently disabling remote DB calls to maintain 0ms latency.")
                    self._circuit_open = True
                    return None
                resp.raise_for_status()
                data = resp.json()
                return data[0] if isinstance(data, list) and data else record
        except Exception as e:
            logger.debug(f"Supabase write skipped: {e}")
            return None

    async def select(self, table: str, params: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
        """Query records from a Supabase table."""
        if not self.enabled:
            return []
        endpoint = f"{self.url.rstrip('/')}/rest/v1/{table}"
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                resp = await client.get(endpoint, headers=self._headers(), params=params or {})
                if resp.status_code == 401:
                    self._circuit_open = True
                    return []
                resp.raise_for_status()
                return resp.json()
        except Exception as e:
            logger.debug(f"Supabase query skipped: {e}")
            return []


supabase_client = SupabaseClient()

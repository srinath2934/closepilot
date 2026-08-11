"""Research Agent: Queries HubSpot CRM data through MCP boundary."""
import asyncio
import logging
from app.graph.state import SalesState
from app.mcp.hubspot import hubspot_client

logger = logging.getLogger("sales_copilot.nodes.research")


async def research_node(state: SalesState) -> SalesState:
    """Retrieve deals and contacts from HubSpot MCP concurrently."""
    logger.info("Executing Research Node: Ingesting HubSpot CRM evidence.")
    try:
        # Fetch deals and contacts concurrently for minimum latency
        deals_task = hubspot_client.get_deals()
        contacts_task = hubspot_client.get_contacts()
        deals, contacts = await asyncio.gather(deals_task, contacts_task)
        
        state["deals"] = deals
        state["contacts"] = contacts
        state["activities"] = []
        
        # Fire-and-forget background audit log to prevent blocking user response
        from app.database.repositories.audit import audit_repo
        thread_id = state.get("thread_id") or state.get("user_request", "default_thread")
        asyncio.create_task(
            audit_repo.log_event(
                thread_id=thread_id,
                node="research",
                action="CRM_INGESTION",
                metadata={"deals_count": len(deals), "contacts_count": len(contacts)}
            )
        )
    except Exception as e:
        logger.error(f"Error during CRM research: {e}")
        state["errors"].append(f"Research node error: {str(e)}")
        
    return state

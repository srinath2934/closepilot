"""FastAPI Backend Entry Point for GWC AI Sales Agent."""
import os
import re
import uuid
import logging
import hashlib
import base64
import secrets
from typing import Optional, Dict, Any
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.config.settings import settings, get_settings
from app.graph.graph import sales_graph
from app.mcp.hubspot import hubspot_client

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("sales_copilot.api")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Stateful AI Sales Intelligence Agent with HubSpot MCP and Human-in-the-Loop approval."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# PKCE Session Cache
PKCE_SESSIONS: Dict[str, str] = {}


def generate_pkce_pair():
    """Generates code_verifier and S256 code_challenge for HubSpot PKCE OAuth."""
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode('utf-8')).digest()
    challenge = base64.urlsafe_b64encode(digest).decode('utf-8').replace('=', '')
    return verifier, challenge


@app.get("/oauth/login")
async def hubspot_oauth_login():
    """Initiates HubSpot PKCE OAuth Flow."""
    current_settings = get_settings()
    client_id = current_settings.HUBSPOT_CLIENT_ID
    if not client_id:
        raise HTTPException(status_code=400, detail="HUBSPOT_CLIENT_ID not configured in .env")
        
    verifier, challenge = generate_pkce_pair()
    session_state = secrets.token_urlsafe(16)
    PKCE_SESSIONS[session_state] = verifier
    
    redirect_uri = f"http://localhost:{current_settings.BACKEND_PORT}/oauth/callback"
    scopes = "crm.objects.deals.read crm.objects.deals.write crm.objects.contacts.read crm.objects.contacts.write"
    
    auth_url = (
        f"https://app.hubspot.com/oauth/authorize"
        f"?client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
        f"&scope={scopes.replace(' ', '%20')}"
        f"&code_challenge={challenge}"
        f"&code_challenge_method=S256"
        f"&state={session_state}"
    )
    return RedirectResponse(auth_url)


@app.get("/oauth/callback")
async def hubspot_oauth_callback(code: str, state: str):
    """Handles OAuth callback, exchanges code & verifier for live HubSpot Access Token."""
    verifier = PKCE_SESSIONS.get(state)
    if not verifier:
        raise HTTPException(status_code=400, detail="Invalid or expired PKCE state session.")
        
    current_settings = get_settings()
    token_url = "https://api.hubapi.com/oauth/v1/token"
    redirect_uri = f"http://localhost:{current_settings.BACKEND_PORT}/oauth/callback"
    
    payload = {
        "grant_type": "authorization_code",
        "client_id": current_settings.HUBSPOT_CLIENT_ID,
        "client_secret": current_settings.HUBSPOT_CLIENT_SECRET,
        "redirect_uri": redirect_uri,
        "code": code,
        "code_verifier": verifier
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(token_url, data=payload)
            resp.raise_for_status()
            data = resp.json()
            
            access_token = data.get("access_token")
            if access_token:
                hubspot_client.access_token = access_token
                hubspot_client.use_mock = False
                settings.HUBSPOT_ACCESS_TOKEN = access_token
                settings.HUBSPOT_USE_MOCK = False
                logger.info("Successfully acquired live HubSpot OAuth Access Token!")
                
                # Persist to .env file for Streamlit and future restarts
                env_path = os.path.join(os.path.dirname(__file__), "../.env")
                try:
                    if os.path.exists(env_path):
                        with open(env_path, "r", encoding="utf-8") as f:
                            content = f.read()
                        import re
                        content = re.sub(r"HUBSPOT_ACCESS_TOKEN=.*", f"HUBSPOT_ACCESS_TOKEN={access_token}", content)
                        content = re.sub(r"HUBSPOT_USE_MOCK=.*", "HUBSPOT_USE_MOCK=false", content)
                        with open(env_path, "w", encoding="utf-8") as f:
                            f.write(content)
                except Exception as env_err:
                    logger.warning(f"Could not persist access token to .env: {env_err}")
                
                return HTMLResponse("""
                <div style="font-family: sans-serif; text-align: center; padding: 50px;">
                    <h1 style="color: #10b981;">🎉 Connected to HubSpot Live CRM!</h1>
                    <p>Your AI Sales Agent is now authenticated with HubSpot Remote MCP.</p>
                    <p>You can close this tab and return to your Streamlit dashboard.</p>
                </div>
                """)
            else:
                raise Exception("No access token returned.")
    except Exception as e:
        logger.error(f"OAuth token exchange failed: {e}")
        return HTMLResponse(f"""
        <div style="font-family: sans-serif; text-align: center; padding: 50px;">
            <h1 style="color: #ef4444;">OAuth Token Exchange Failed</h1>
            <p>{str(e)}</p>
        </div>
        """, status_code=500)


# Request & Response Schemas
class StartWorkflowRequest(BaseModel):
    user_request: str = "Who should I follow up with today?"
    thread_id: Optional[str] = None


class ApproveWorkflowRequest(BaseModel):
    thread_id: str
    action: str  # "APPROVED" | "REJECTED" | "MODIFIED"
    modified_subject: Optional[str] = None
    modified_body: Optional[str] = None


@app.get("/")
async def root():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "llm_provider": settings.LLM_PROVIDER,
        "mcp_mode": "Mock/Sandbox" if settings.HUBSPOT_USE_MOCK else "Live HubSpot Remote MCP"
    }


@app.get("/api/health")
async def health_check():
    """Comprehensive health check with HubSpot connection test."""
    current_settings = get_settings()
    is_live = not current_settings.HUBSPOT_USE_MOCK and bool(current_settings.HUBSPOT_ACCESS_TOKEN)
    
    hubspot_status = "disconnected"
    hubspot_detail = "Using sandbox mode"
    if is_live:
        try:
            headers = {"Authorization": f"Bearer {current_settings.HUBSPOT_ACCESS_TOKEN}"}
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(
                    "https://api.hubapi.com/crm/v3/objects/deals?limit=1",
                    headers=headers,
                )
                if resp.status_code == 200:
                    hubspot_status = "connected"
                    hubspot_detail = "Live HubSpot API responding"
                elif resp.status_code == 401:
                    hubspot_status = "auth_expired"
                    hubspot_detail = "OAuth token expired - re-authenticate"
                else:
                    hubspot_status = "error"
                    hubspot_detail = f"API returned {resp.status_code}"
        except Exception as e:
            hubspot_status = "unreachable"
            hubspot_detail = str(e)

    supabase_status = "disabled"
    if current_settings.SUPABASE_URL and current_settings.SUPABASE_KEY:
        supabase_status = "configured"

    return {
        "status": "healthy",
        "llm_provider": current_settings.LLM_PROVIDER,
        "llm_model": current_settings.LLM_MODEL,
        "hubspot": {"status": hubspot_status, "detail": hubspot_detail, "live": is_live},
        "supabase": {"status": supabase_status, "url": current_settings.SUPABASE_URL or "not configured"},
    }


@app.get("/api/settings")
async def get_current_settings_endpoint():
    """Expose current configuration (redacted secrets)."""
    current_settings = get_settings()
    return {
        "llm_provider": current_settings.LLM_PROVIDER,
        "llm_model": current_settings.LLM_MODEL,
        "hubspot_use_mock": current_settings.HUBSPOT_USE_MOCK,
        "hubspot_has_token": bool(current_settings.HUBSPOT_ACCESS_TOKEN),
        "hubspot_app_id": current_settings.HUBSPOT_APP_ID,
        "supabase_configured": bool(current_settings.SUPABASE_URL and current_settings.SUPABASE_KEY),
        "backend_port": current_settings.BACKEND_PORT,
    }


class SeedDealRequest(BaseModel):
    deal_name: str
    amount: float
    stage: str = "qualifiedtobuy"
    close_date: Optional[str] = None


@app.post("/api/deals/seed")
async def seed_deal(req: SeedDealRequest):
    """Seed a test deal into HubSpot CRM (sandbox or live)."""
    try:
        new_deal = await hubspot_client.create_deal(
            deal_name=req.deal_name,
            amount=req.amount,
            stage=req.stage,
            close_date=req.close_date,
        )
        return {"status": "created", "deal": new_deal}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/deals")
async def get_crm_deals():
    """Retrieve raw CRM deals from HubSpot MCP."""
    deals = await hubspot_client.get_deals()
    return {"deals": deals, "total": len(deals)}



@app.post("/api/workflow/start")
async def start_workflow(req: StartWorkflowRequest):
    """
    Start LangGraph sales intelligence workflow.
    Executes through research -> prioritize -> strategy -> communication -> pauses at approval.
    """
    thread_id = req.thread_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    initial_state = {
        "thread_id": thread_id,
        "user_request": req.user_request,
        "intent": "FIND_FOLLOWUPS",
        "deals": [],
        "contacts": [],
        "activities": [],
        "opportunities": [],
        "selected_opportunity": None,
        "priority_score": None,
        "strategy": None,
        "followup_draft": None,
        "approval_status": None,
        "action_result": None,
        "verification_result": None,
        "errors": [],
        "retry_count": 0
    }
    
    logger.info(f"Starting workflow for thread {thread_id} with request: {req.user_request}")
    
    try:
        # Run graph until interrupt at approval node
        result = await sales_graph.ainvoke(initial_state, config=config)
        return {
            "thread_id": thread_id,
            "status": "AWAITING_HUMAN_APPROVAL",
            "state": result
        }
    except Exception as e:
        logger.error(f"Workflow start failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/workflow/approve")
async def approve_workflow(req: ApproveWorkflowRequest):
    """
    Submit human approval or modifications to resume workflow execution.
    Executes action -> verification -> END.
    """
    config = {"configurable": {"thread_id": req.thread_id}}
    
    # Check current thread state
    current_state = await sales_graph.aget_state(config)
    if not current_state or not current_state.values:
        raise HTTPException(status_code=404, detail="Workflow thread not found.")
        
    update_payload = {"approval_status": req.action.upper()}
    if req.modified_subject and req.modified_body:
        update_payload["followup_draft"] = {
            "subject": req.modified_subject,
            "body": req.modified_body,
            "action_type": "CREATE_CRM_TASK_AND_DRAFT_EMAIL"
        }

    logger.info(f"Resuming thread {req.thread_id} with approval status: {req.action}")
    
    try:
        await sales_graph.aupdate_state(config, update_payload, as_node="communication")
        resumed_result = await sales_graph.ainvoke(None, config=config)
        return {
            "thread_id": req.thread_id,
            "status": "COMPLETED" if req.action.upper() in ["APPROVED", "MODIFIED"] else "CANCELLED",
            "state": resumed_result
        }
    except Exception as e:
        logger.error(f"Approval resume failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/workflow/status/{thread_id}")
async def get_workflow_status(thread_id: str):
    """Get the current state of a workflow thread."""
    config = {"configurable": {"thread_id": thread_id}}
    current_state = await sales_graph.aget_state(config)
    if not current_state or not current_state.values:
        raise HTTPException(status_code=404, detail="Thread not found.")
    return {
        "thread_id": thread_id,
        "next_nodes": current_state.next,
        "state": current_state.values
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.BACKEND_HOST, port=settings.BACKEND_PORT, reload=True)

"""Streamlit Frontend Application for GWC AI Sales Agent.
Comprehensive Enterprise UI: Copilot Workflow, Live Pipeline Explorer, Deal Creator, Audit Log, and Settings.
"""
import sys
import os
from dotenv import load_dotenv
load_dotenv(override=True)

# Ensure root workspace directory is on sys.path for streamlit
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.config.settings import Settings, get_settings
get_settings()  # Exports LANGCHAIN_TRACING_V2 & LANGCHAIN_API_KEY

import nest_asyncio
nest_asyncio.apply()

import streamlit as st
import asyncio
import uuid
import logging
from datetime import datetime, timedelta

from app.graph.graph import sales_graph
from app.mcp.hubspot import hubspot_client
from app.config.settings import Settings, get_settings
from app.graph.nodes.strategy import strategy_node
from app.graph.nodes.communication import communication_node

logger = logging.getLogger("sales_copilot.frontend")

st.set_page_config(
    page_title="ClosePilot • AI Sales Follow-Up Copilot",
    page_icon=":material/bolt:",
    layout="wide",
    initial_sidebar_state="expanded",
)


def get_current_settings():
    try:
        return get_settings()
    except Exception:
        from app.config.settings import settings
        return settings


def run_async(coro):
    """Safely run an async coroutine inside Streamlit's event loop."""
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(coro)


current_settings = get_current_settings()

# ---------------------------------------------------------------------------
# Session State Initialization
# ---------------------------------------------------------------------------
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
if "workflow_state" not in st.session_state:
    st.session_state.workflow_state = None
if "execution_phase" not in st.session_state:
    st.session_state.execution_phase = "IDLE"  # "IDLE" | "AWAITING_APPROVAL" | "COMPLETED"
if "last_error" not in st.session_state:
    st.session_state.last_error = None
if "crm_source" not in st.session_state:
    st.session_state.crm_source = None
if "active_tab" not in st.session_state:
    st.session_state.active_tab = 0

# ---------------------------------------------------------------------------
# Sidebar - Global Health & Navigation
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title(":material/bolt: ClosePilot")
    st.caption("Autonomous CRM Intelligence & Human-in-the-Loop Follow-Up")
    st.divider()

    is_live_mcp = not current_settings.HUBSPOT_USE_MOCK and bool(current_settings.HUBSPOT_ACCESS_TOKEN)

    st.subheader("System status")
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        st.metric("LLM Provider", current_settings.LLM_PROVIDER.upper())
    with col_s2:
        st.metric("CRM Mode", "Live" if is_live_mcp else "Sandbox")

    if is_live_mcp:
        st.success(":material/cloud_done: Connected to HubSpot Live CRM", icon=":material/check_circle:")
    else:
        st.warning("Using sandbox CRM data (mock mode)", icon=":material/warning:")

    st.divider()
    st.subheader("Live integrations")
    st.link_button(
        ":material/key: Reconnect HubSpot (OAuth)",
        url=f"http://localhost:{current_settings.BACKEND_PORT}/oauth/login",
    )

    st.divider()
    st.subheader("Session control")
    st.caption(f"Active Thread: `{st.session_state.thread_id[:12]}...`")
    if st.button(":material/refresh: New session / Reset", type="secondary"):
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.workflow_state = None
        st.session_state.execution_phase = "IDLE"
        st.session_state.last_error = None
        st.session_state.crm_source = None
        st.rerun()

# ---------------------------------------------------------------------------
# Top Header & Pipeline Visualizer
# ---------------------------------------------------------------------------
st.title(":material/target: AI Sales Intelligence & Follow-Up Copilot")
st.caption("Deterministic CRM prioritization • LLM strategic reasoning • Human approval gate • HubSpot MCP execution")

# Main Navigation Tabs
tab_copilot, tab_explorer, tab_create_deal, tab_audit = st.tabs([
    ":material/psychology: AI Copilot & Follow-Ups",
    ":material/table_chart: Live CRM Explorer",
    ":material/add_circle: Create CRM Deal",
    ":material/history: Audit & Security Trail",
])

# ===========================================================================
# TAB 1: UNIFIED AI COPILOT CHAT (AGENT PLUS STYLE)
# ===========================================================================
with tab_copilot:
    # Top Visualizer Bar
    phase = st.session_state.execution_phase
    steps = [
        ("1. Read CRM", phase in ("AWAITING_APPROVAL", "COMPLETED")),
        ("2. Prioritize", phase in ("AWAITING_APPROVAL", "COMPLETED")),
        ("3. Reason & Draft", phase in ("AWAITING_APPROVAL", "COMPLETED")),
        ("4. Human Approval", phase == "AWAITING_APPROVAL"),
        ("5. Act & Verify", phase == "COMPLETED"),
    ]
    step_cols = st.columns(len(steps))
    for col, (label, is_active) in zip(step_cols, steps):
        col.button(
            label,
            type="primary" if is_active else "secondary",
            disabled=True,
            key=f"step_btn_{label}",
            use_container_width=True
        )

    st.divider()

    # Suggested Action Chips
    st.markdown("##### 💡 Suggested Actions")
    q1, q2, q3, q4 = st.columns(4)
    quick_input = None
    if q1.button("🎯 Analyze Enterprise Deals ($50k+)", use_container_width=True):
        quick_input = "Find urgent enterprise deals worth $50,000 or more"
    if q2.button("⏳ Find Stalled Opportunities (>3 Days)", use_container_width=True):
        quick_input = "Find stalled opportunities inactive for more than 3 days"
    if q3.button("📝 Closing Follow-Ups (Contract Sent)", use_container_width=True):
        quick_input = "Find deals at Contract Sent stage needing closing follow-up"
    if q4.button("⚡ Run Daily Prioritization", use_container_width=True):
        quick_input = "Who should I follow up with today?"

    st.divider()

    # Chat Messages History Initialization
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = [
            {
                "role": "assistant",
                "content": "👋 Welcome to **ClosePilot**! I am your autonomous AI Sales Intelligence & Follow-Up Copilot.\n\nYou can chat with me naturally or give commands like:\n* 🔍 *'Who should I follow up with today?'*\n* 🎯 *'Find high-value enterprise deals over $50k'*\n* ⏳ *'Diagnose why Acme Corp deal has stalled for 6 days'*\n* 📝 *'Show me deals at the Contract Sent stage'*\n* ✍️ *'Make the follow-up email under 60 words'*",
                "workflow_state": None
            }
        ]

    # Render Chat Messages Stream
    for idx, msg in enumerate(st.session_state.chat_messages):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

            # If this message contains an active workflow state, render the interactive Agent Card!
            wf_state = msg.get("workflow_state")
            if wf_state:
                opps = wf_state.get("opportunities", [])
                selected_opp = wf_state.get("selected_opportunity") or {}
                strategy = wf_state.get("strategy") or {}
                draft = wf_state.get("followup_draft") or {}

                with st.container(border=True):
                    col_left, col_right = st.columns([1, 1.25])

                    # LEFT: Ranked Opportunities
                    with col_left:
                        st.subheader(":material/leaderboard: Ranked CRM Opportunities")
                        for i, opp in enumerate(opps):
                            is_selected = str(opp.get("id")) == str(selected_opp.get("id"))
                            marker = ":material/star:" if is_selected else f"{i + 1}."
                            with st.container(border=True):
                                h_c, s_c = st.columns([3, 1])
                                with h_c:
                                    st.markdown(f"**{marker} {opp.get('name')}**")
                                    st.caption(f"{opp.get('contact_name')} ({opp.get('contact_title')}) • {opp.get('company_name')}")
                                with s_c:
                                    st.metric("Score", f"{opp.get('score', 0):.0f}")

                                m1, m2, m3 = st.columns(3)
                                m1.markdown(f"`${opp.get('amount', 0):,.0f}`")
                                m2.markdown(f"`{opp.get('stage')}`")
                                m3.markdown(f"`{opp.get('days_inactive', 0)}d inactive`")

                                with st.expander("Score Breakdown & Facts", expanded=False):
                                    for r in opp.get("score_reasons", []):
                                        st.markdown(f"• `{r}`")
                                    for n in opp.get("notes", []):
                                        st.markdown(f"• {n}")

                                if not is_selected and st.session_state.execution_phase == "AWAITING_APPROVAL":
                                    if st.button(f":material/alt_route: Select {opp.get('name')[:18]}...", key=f"chat_sel_{idx}_{opp.get('id')}", use_container_width=True):
                                        config = {"configurable": {"thread_id": st.session_state.thread_id}}
                                        wf_state["selected_opportunity"] = opp
                                        wf_state["priority_score"] = opp.get("score")
                                        up_state = run_async(strategy_node(wf_state))
                                        up_state = run_async(communication_node(up_state))
                                        run_async(
                                            sales_graph.aupdate_state(
                                                config,
                                                {
                                                    "selected_opportunity": opp,
                                                    "priority_score": opp.get("score"),
                                                    "strategy": up_state.get("strategy"),
                                                    "followup_draft": up_state.get("followup_draft"),
                                                },
                                                as_node="prioritize"
                                            )
                                        )
                                        msg["workflow_state"] = up_state
                                        st.session_state.workflow_state = up_state
                                        st.rerun()

                    # RIGHT: Strategy & Approval Gate
                    with col_right:
                        st.subheader(":material/psychology: Strategy & Follow-Up Gate")
                        with st.container(border=True):
                            st.markdown(f":material/play_arrow: **Recommended Action:** `{strategy.get('recommended_action', 'SEND_FOLLOWUP_EMAIL')}`")
                            st.markdown(f"**Rationale:** {strategy.get('rationale', 'N/A')}")

                        st.markdown("#### :material/edit: Grounded Follow-Up Draft (Editable)")
                        edit_subject = st.text_input("Subject Line:", value=draft.get("subject", ""), key=f"chat_subj_{idx}")
                        edit_body = st.text_area("Email Content:", value=draft.get("body", ""), height=180, key=f"chat_body_{idx}")

                        if st.session_state.execution_phase == "AWAITING_APPROVAL":
                            # AI Revision Assistant
                            with st.expander(":material/auto_awesome: Instruct Copilot to Revise Draft / Tone", expanded=False):
                                rev_c1, rev_c2 = st.columns([3, 1])
                                with rev_c1:
                                    rev_inst = st.text_input("Instruction:", placeholder="e.g. Keep under 75 words and emphasize ROI", key=f"chat_rev_{idx}", label_visibility="collapsed")
                                with rev_c2:
                                    if st.button(":material/refresh: Re-draft", key=f"chat_rev_btn_{idx}", use_container_width=True):
                                        if rev_inst:
                                            temp_state = wf_state.copy()
                                            temp_state["user_request"] = rev_inst
                                            up_comm = run_async(communication_node(temp_state))
                                            if up_comm.get("followup_draft"):
                                                msg["workflow_state"]["followup_draft"] = up_comm.get("followup_draft")
                                                st.session_state.workflow_state["followup_draft"] = up_comm.get("followup_draft")
                                                st.rerun()

                            st.info(":material/warning: **Human Approval Required:** Review or edit above before writing to HubSpot.")
                            b1, b2 = st.columns(2)
                            with b1:
                                if st.button(":material/check_circle: Approve & Write to HubSpot", type="primary", key=f"chat_appr_{idx}", use_container_width=True):
                                    config = {"configurable": {"thread_id": st.session_state.thread_id}}
                                    update_payload = {
                                        "approval_status": "APPROVED",
                                        "selected_opportunity": selected_opp,
                                        "followup_draft": {
                                            "subject": edit_subject,
                                            "body": edit_body,
                                            "action_type": "CREATE_CRM_TASK_AND_DRAFT_EMAIL",
                                        },
                                    }
                                    run_async(sales_graph.aupdate_state(config, update_payload, as_node="communication"))
                                    final_result = run_async(sales_graph.ainvoke(None, config=config))
                                    msg["workflow_state"] = final_result
                                    st.session_state.workflow_state = final_result
                                    st.session_state.execution_phase = "COMPLETED"

                                    act_res = final_result.get("action_result") or {}
                                    st.session_state.chat_messages.append({
                                        "role": "assistant",
                                        "content": f"🎉 **Execution Approved & Verified in HubSpot CRM!**\n\n• **HubSpot Task ID:** `{act_res.get('task_id', 'N/A')}`\n• **HubSpot Note ID:** `{act_res.get('note_id', 'N/A')}`\n• **Status:** `{final_result.get('verification_result', {}).get('status', 'VERIFIED')}`\n\nThe follow-up task and note have been persisted to your CRM pipeline.",
                                        "workflow_state": None
                                    })
                                    st.rerun()

                            with b2:
                                if st.button(":material/cancel: Reject / Skip Action", key=f"chat_rej_{idx}", use_container_width=True):
                                    config = {"configurable": {"thread_id": st.session_state.thread_id}}
                                    run_async(sales_graph.aupdate_state(config, {"approval_status": "REJECTED"}, as_node="communication"))
                                    final_result = run_async(sales_graph.ainvoke(None, config=config))
                                    msg["workflow_state"] = final_result
                                    st.session_state.workflow_state = final_result
                                    st.session_state.execution_phase = "COMPLETED"
                                    st.session_state.chat_messages.append({
                                        "role": "assistant",
                                        "content": "🛑 **Action Cancelled / Skipped.** No writes were made to HubSpot CRM.",
                                        "workflow_state": None
                                    })
                                    st.rerun()

                        elif st.session_state.execution_phase == "COMPLETED":
                            if wf_state.get("approval_status") in ("APPROVED", "MODIFIED"):
                                st.success(":material/check_circle: **Action Completed & Verified in HubSpot CRM!**")
                            else:
                                st.warning("🛑 **Action was skipped.**")

    # Unified Chat Input Bar
    chat_prompt = st.chat_input("Chat with ClosePilot (e.g. 'Analyze my pipeline', 'Why is Acme Corp prioritized?', 'Make draft shorter')...")
    
    # Check if a quick button was clicked
    active_chat_input = chat_prompt or quick_input

    if active_chat_input:
        st.session_state.chat_messages.append({"role": "user", "content": active_chat_input, "workflow_state": None})
        input_lower = active_chat_input.lower().strip(" \"'\t\r\n")

        # Intent Detection
        is_analysis_intent = any(
            kw in input_lower for kw in [
                "analyze", "follow up", "followup", "who should i", "priority", "prioritize",
                "find deal", "find urgent", "enterprise deal", "stalled deal", "opportunities",
                "pipeline review", "run workflow", "which deal", "today"
            ]
        )

        is_revision_intent = any(
            kw in input_lower for kw in [
                "rewrite", "revise", "make it shorter", "make draft", "shorter", "change tone",
                "add discount", "friendlier", "more concise", "update draft", "re-draft", "mention"
            ]
        ) and st.session_state.workflow_state is not None

        if is_analysis_intent:
            with st.chat_message("user"):
                st.markdown(active_chat_input)

            with st.chat_message("assistant"):
                with st.spinner(f"ClosePilot is executing multi-agent pipeline for '{active_chat_input}'..."):
                    try:
                        config = {"configurable": {"thread_id": st.session_state.thread_id}}
                        initial_state = {
                            "thread_id": st.session_state.thread_id,
                            "user_request": active_chat_input,
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
                            "retry_count": 0,
                        }
                        result = run_async(sales_graph.ainvoke(initial_state, config=config))
                        deals = result.get("deals", [])
                        selected = result.get("selected_opportunity") or {}

                        has_live_ids = any(str(d.get("id", "")).isdigit() for d in deals)
                        st.session_state.crm_source = "Live HubSpot" if has_live_ids else "Sandbox"
                        st.session_state.workflow_state = result
                        st.session_state.execution_phase = "AWAITING_APPROVAL"

                        reply_text = f"✅ **Analysis Complete!** Evaluated **{len(deals)} active CRM deals**.\n\n🎯 **Top Priority:** **{selected.get('name', 'N/A')}** (${float(selected.get('amount', 0)):,.0f} • `{selected.get('stage', 'N/A')}`)\n• **Score:** `{selected.get('score', 0):.0f} pts`\n• **Contact:** {selected.get('contact_name')} ({selected.get('contact_title')})\n\n👉 *Review and approve the follow-up below:*"
                        st.session_state.chat_messages.append({
                            "role": "assistant",
                            "content": reply_text,
                            "workflow_state": result
                        })
                        st.rerun()
                    except Exception as e:
                        err_msg = f"Analysis workflow failed: {e}"
                        st.error(err_msg)
                        st.session_state.chat_messages.append({"role": "assistant", "content": err_msg, "workflow_state": None})

        elif is_revision_intent:
            with st.chat_message("user"):
                st.markdown(active_chat_input)

            with st.chat_message("assistant"):
                with st.spinner("Revising follow-up email draft with your instructions..."):
                    try:
                        temp_state = st.session_state.workflow_state.copy()
                        temp_state["user_request"] = active_chat_input
                        updated_comm = run_async(communication_node(temp_state))
                        if updated_comm.get("followup_draft"):
                            st.session_state.workflow_state["followup_draft"] = updated_comm.get("followup_draft")
                            rev_draft = updated_comm.get("followup_draft")
                            reply_text = f"✨ **Draft Revised Successfully!**\n\n**Subject:** {rev_draft.get('subject')}\n\n```text\n{rev_draft.get('body')}\n```\n\n*The review card has been updated. You can approve and write it to HubSpot whenever you are ready!*"
                            st.session_state.chat_messages.append({
                                "role": "assistant",
                                "content": reply_text,
                                "workflow_state": st.session_state.workflow_state
                            })
                            st.rerun()
                    except Exception as e:
                        err_msg = f"Draft revision failed: {e}"
                        st.error(err_msg)
                        st.session_state.chat_messages.append({"role": "assistant", "content": err_msg, "workflow_state": None})

        else:
            # General Conversational & Diagnostic Query
            with st.chat_message("user"):
                st.markdown(active_chat_input)

            with st.chat_message("assistant"):
                with st.spinner("ClosePilot is analyzing CRM pipeline context with NVIDIA LLM..."):
                    try:
                        from app.llm.provider import get_llm_provider
                        
                        active_opps = []
                        if st.session_state.workflow_state:
                            active_opps = st.session_state.workflow_state.get("opportunities", [])
                        if not active_opps:
                            active_opps = run_async(hubspot_client.get_deals())

                        context_lines = []
                        for o in active_opps[:10]:
                            notes_str = " | Notes: " + " ".join(o.get("notes", [])) if o.get("notes") else ""
                            context_lines.append(
                                f"• Deal: {o.get('name')} | Stage: {o.get('stage')} | Amount: ${float(o.get('amount', 0)):,.0f} | Inactive: {o.get('days_inactive', 0)} days | Contact: {o.get('contact_name')} ({o.get('contact_title')}, {o.get('company_name')}){notes_str}"
                            )
                        pipeline_context = "\n".join(context_lines)

                        chat_system_prompt = f"""You are ClosePilot, an elite AI Sales Intelligence & Revenue Operations Copilot.
You have real-time access to the user's HubSpot CRM pipeline:

### ACTIVE CRM PIPELINE:
{pipeline_context}

### INSTRUCTIONS:
- Answer the user's strategic questions, diagnose deal bottlenecks, explain prioritization rankings, or suggest outreach angles.
- Ground all facts strictly in the CRM data above.
- Be concise, analytical, and actionable. Provide bullet points and clear next steps."""

                        llm = get_llm_provider()
                        ai_reply = run_async(llm.generate(chat_system_prompt, active_chat_input))
                        st.markdown(ai_reply)
                        st.session_state.chat_messages.append({"role": "assistant", "content": ai_reply, "workflow_state": None})
                    except Exception as e:
                        err_msg = f"Chat analysis error: {e}"
                        st.error(err_msg)
                        st.session_state.chat_messages.append({"role": "assistant", "content": err_msg, "workflow_state": None})


# ===========================================================================
# TAB 2: LIVE CRM PIPELINE EXPLORER
# ===========================================================================
with tab_explorer:
    st.subheader(":material/table_chart: Live HubSpot Deals & Contacts Explorer")
    st.caption("Direct read-only inspection of objects currently active in your HubSpot CRM account.")

    exp_col1, exp_col2 = st.columns([3, 1])
    with exp_col2:
        if st.button(":material/refresh: Refresh Live Deals", key="btn_refresh_deals"):
            st.rerun()

    try:
        live_deals = run_async(hubspot_client.get_deals())
        live_contacts = run_async(hubspot_client.get_contacts())

        tab_deals_view, tab_contacts_view = st.tabs([
            f":material/payments: Active Deals ({len(live_deals)})",
            f":material/people: Registered Contacts ({len(live_contacts)})"
        ])

        with tab_deals_view:
            for deal in live_deals:
                with st.container(border=True):
                    d_c1, d_c2, d_c3, d_c4 = st.columns([2.5, 1.5, 1.5, 1.5])
                    d_c1.markdown(f"**{deal.get('name')}** (ID: `{deal.get('id')}`)")
                    d_c2.markdown(f"**Amount:** `${deal.get('amount', 0):,.0f}`")
                    d_c3.markdown(f"**Stage:** `{deal.get('stage')}`")
                    d_c4.markdown(f"**Inactive:** `{deal.get('days_inactive', 0)} days`")
                    
                    st.caption(f"Associated Contact: {deal.get('contact_name')} ({deal.get('contact_email')}) • Company: {deal.get('company_name')}")
                    if deal.get("notes"):
                        st.markdown(f"*Notes:* {deal.get('notes')[0]}")

        with tab_contacts_view:
            for contact in live_contacts:
                with st.container(border=True):
                    c1, c2, c3 = st.columns([2, 2, 2])
                    c1.markdown(f"**{contact.get('name')}**")
                    c2.markdown(f"Email: `{contact.get('email')}`")
                    c3.markdown(f"Title: `{contact.get('title')}` ({contact.get('company')})")

    except Exception as e:
        st.error(f"Could not load live CRM objects: {e}")


# ===========================================================================
# TAB 3: CREATE & SEED CRM DEALS DIRECTLY IN HUBSPOT
# ===========================================================================
with tab_create_deal:
    st.subheader(":material/add_circle: Create New Deal in HubSpot CRM")
    st.caption("Instantly inject a new deal with custom value, stage, and contact into your live CRM pipeline.")

    with st.form("create_new_deal_form"):
        form_c1, form_c2 = st.columns(2)
        with form_c1:
            new_deal_name = st.text_input("Deal Name:", placeholder="e.g. Acme Corp Enterprise AI Platform")
            new_deal_amount = st.number_input("Target Contract Value ($):", min_value=1000.0, value=50000.0, step=5000.0)
        with form_c2:
            new_deal_stage = st.selectbox(
                "Deal Stage:",
                options=[
                    "4131145421",  # Contract Sent
                    "4131145420",  # Decision Maker Bought-In
                    "4131145419",  # Presentation Scheduled
                    "4131145418",  # Qualified to Buy
                ],
                format_func=lambda x: {
                    "4131145421": "Contract Sent (High Intent)",
                    "4131145420": "Decision Maker Bought-In",
                    "4131145419": "Presentation Scheduled",
                    "4131145418": "Qualified to Buy",
                }.get(x, x)
            )
            new_deal_close = st.date_input("Target Close Date:", value=datetime.now() + timedelta(days=30))

        submit_deal = st.form_submit_button(":material/send: Create Deal in HubSpot", type="primary")

        if submit_deal:
            if not new_deal_name.strip():
                st.error("Please enter a deal name.")
            else:
                with st.spinner(f"Writing {new_deal_name} to HubSpot CRM..."):
                    try:
                        res = run_async(
                            hubspot_client.create_deal(
                                deal_name=new_deal_name,
                                amount=new_deal_amount,
                                stage=new_deal_stage,
                                close_date=new_deal_close.strftime("%Y-%m-%d"),
                            )
                        )
                        st.success(f"🎉 Deal created successfully with ID: `{res.get('id')}`")
                    except Exception as e:
                        st.error(f"Failed to create deal: {e}")


# ===========================================================================
# TAB 4: AUDIT & SECURITY TRAIL
# ===========================================================================
with tab_audit:
    st.subheader(":material/history: System Audit & Compliance Trail")
    st.caption("Immutable record of agent executions, human approvals, and CRM tool invocations.")

    st.markdown("#### Logged Agent Actions & Verified Writes")
    if hasattr(hubspot_client, "_logged_tasks") and hubspot_client._logged_tasks:
        for t in reversed(hubspot_client._logged_tasks):
            with st.container(border=True):
                st.markdown(f"**Task ID:** `{t.get('task_id')}` | **Deal:** `{t.get('deal_id')}` | **Status:** `{t.get('status')}`")
                st.markdown(f"**Subject:** {t.get('subject')}")
                st.caption(f"Created: {t.get('created_at')} • Due: {t.get('due_date')}")
    else:
        st.info("No write actions logged yet in this session. Run the workflow and approve a task to see real-time audit records.")




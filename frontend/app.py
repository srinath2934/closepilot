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
tab_copilot, tab_explorer, tab_create_deal, tab_audit, tab_settings = st.tabs([
    ":material/psychology: AI Copilot & Follow-Ups",
    ":material/table_chart: Live CRM Explorer",
    ":material/add_circle: Create CRM Deal",
    ":material/history: Audit & Security Trail",
    ":material/settings: Settings & Health",
])

# ===========================================================================
# TAB 1: AI COPILOT & HUMAN-IN-THE-LOOP FOLLOW-UP WORKFLOW
# ===========================================================================
with tab_copilot:
    # Visualizer Bar
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
        )

    st.divider()

    # Quick Prompt Chips
    if "active_prompt" not in st.session_state:
        st.session_state.active_prompt = "Who should I follow up with today?"

    st.markdown("##### 💡 Suggested Sales Inquiries")
    q1, q2, q3, q4 = st.columns(4)
    if q1.button("🎯 Enterprise Deals ($50k+)", use_container_width=True):
        st.session_state.active_prompt = "Find urgent enterprise deals worth $50,000 or more"
        st.rerun()
    if q2.button("⏳ Stalled Deals (>3 Days)", use_container_width=True):
        st.session_state.active_prompt = "Find stalled opportunities inactive for more than 3 days"
        st.rerun()
    if q3.button("📝 Contracts Pending Sign", use_container_width=True):
        st.session_state.active_prompt = "Find deals at Contract Sent stage needing closing follow-up"
        st.rerun()
    if q4.button("⚡ Daily Top Priorities", use_container_width=True):
        st.session_state.active_prompt = "Who should I follow up with today?"
        st.rerun()

    # Query Input Section
    with st.container(border=True):
        prompt_col, btn_col = st.columns([4, 1])
        with prompt_col:
            user_prompt = st.text_input(
                "Sales request prompt (Customizable):",
                value=st.session_state.active_prompt,
                placeholder="e.g. Find urgent follow-ups for high-value enterprise pipeline deals or Acme Corp",
                label_visibility="visible",
                key="main_user_prompt_input"
            )
        with btn_col:
            st.write("")  # spacing
            trigger_btn = st.button(":material/play_arrow: Analyze CRM", type="primary", use_container_width=True)

    # Handle Analysis Trigger
    if trigger_btn:
        st.session_state.last_error = None
        with st.status("Analyzing HubSpot CRM deals...", expanded=True) as status:
            st.write(":material/search: Ingesting active pipeline deals and decision-maker contacts...")
            config = {"configurable": {"thread_id": st.session_state.thread_id}}
            initial_state = {
                "thread_id": st.session_state.thread_id,
                "user_request": user_prompt,
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
            try:
                st.write(":material/analytics: Computing deterministic priority scores based on deal value, stage, and inactivity...")
                result = run_async(sales_graph.ainvoke(initial_state, config=config))

                # Identify CRM Source
                deals = result.get("deals", [])
                has_live_ids = any(str(d.get("id", "")).isdigit() for d in deals)
                st.session_state.crm_source = "Live HubSpot" if has_live_ids else "Sandbox"

                st.write(":material/auto_awesome: Synthesizing strategy and generating evidence-grounded follow-up draft...")
                st.session_state.workflow_state = result
                st.session_state.execution_phase = "AWAITING_APPROVAL"
                status.update(
                    label=f"Analysis complete - {len(deals)} deals ranked",
                    state="complete",
                )
                st.rerun()
            except Exception as e:
                logger.error(f"Workflow failed: {e}", exc_info=True)
                st.session_state.last_error = str(e)
                status.update(label="Analysis failed", state="error")
                st.error(f"Workflow execution failed: {e}")

    # Error Notification
    if st.session_state.last_error and phase == "IDLE":
        st.error(f":material/error: {st.session_state.last_error}")

    # Results & Human Review Panel
    if st.session_state.workflow_state:
        state = st.session_state.workflow_state
        opps = state.get("opportunities", [])
        selected_opp = state.get("selected_opportunity")
        strategy = state.get("strategy") or {}
        draft = state.get("followup_draft") or {}
        errors = state.get("errors", [])

        # Data source banner
        if st.session_state.crm_source:
            if st.session_state.crm_source == "Live HubSpot":
                st.success(f":material/cloud_done: Data Source: **{st.session_state.crm_source}** ({len(opps)} opportunities retrieved)")
            else:
                st.info(f":material/database: Data Source: **{st.session_state.crm_source}** ({len(opps)} opportunities retrieved)")

        if errors:
            with st.expander(f":material/warning: {len(errors)} Agent Notice(s)", expanded=False):
                for err in errors:
                    st.warning(err)

        col_left, col_right = st.columns([1, 1.25])

        # LEFT COLUMN: Ranked Opportunity Deck
        with col_left:
            st.subheader(":material/leaderboard: Ranked CRM Opportunities")
            for i, opp in enumerate(opps):
                is_selected = selected_opp and str(opp.get("id")) == str(selected_opp.get("id"))

                with st.container(border=True):
                    h_col, s_col = st.columns([3, 1])
                    with h_col:
                        marker = ":material/star:" if is_selected else f"{i + 1}."
                        st.markdown(f"**{marker} {opp.get('name')}**")
                        st.caption(f"{opp.get('contact_name')} ({opp.get('contact_title')}) • {opp.get('company_name')}")
                    with s_col:
                        st.metric("Score", f"{opp.get('score', 0):.0f}")

                    m1, m2, m3 = st.columns(3)
                    m1.markdown(f"`${opp.get('amount', 0):,.0f}`")
                    m2.markdown(f"`{opp.get('stage')}`")
                    m3.markdown(f"`{opp.get('days_inactive', 0)}d inactive`")

                    with st.expander("View Score Breakdown & CRM Facts"):
                        st.markdown("**Scoring Breakdown:**")
                        for reason in opp.get("score_reasons", []):
                            st.markdown(f"• `{reason}`")
                        st.markdown("**CRM History & Notes:**")
                        for note in opp.get("notes", []):
                            st.markdown(f"• {note}")
                        st.caption(f"Contact Email: `{opp.get('contact_email', 'N/A')}`")

                    # Opportunity Switcher Button
                    if not is_selected and st.session_state.execution_phase == "AWAITING_APPROVAL":
                        if st.button(f":material/alt_route: Select {opp.get('name')[:20]}...", key=f"switch_{opp.get('id')}"):
                            with st.spinner(f"Generating strategy and draft for {opp.get('name')}..."):
                                config = {"configurable": {"thread_id": st.session_state.thread_id}}
                                state["selected_opportunity"] = opp
                                state["priority_score"] = opp.get("score")
                                updated_state = run_async(strategy_node(state))
                                updated_state = run_async(communication_node(updated_state))
                                
                                # Synchronize LangGraph checkpointer state with switched deal
                                run_async(
                                    sales_graph.aupdate_state(
                                        config,
                                        {
                                            "selected_opportunity": opp,
                                            "priority_score": opp.get("score"),
                                            "strategy": updated_state.get("strategy"),
                                            "followup_draft": updated_state.get("followup_draft"),
                                        },
                                        as_node="prioritize"
                                    )
                                )
                                st.session_state.workflow_state = updated_state
                                st.rerun()

        # RIGHT COLUMN: Strategic Rationale & Human Approval Gate
        with col_right:
            st.subheader(":material/psychology: Strategic Analysis & Follow-Up Gate")

            if selected_opp:
                # Strategy Briefing Card
                with st.container(border=True):
                    st.markdown("**Strategy Agent Rationale**")
                    action = strategy.get("recommended_action", "SEND_FOLLOWUP_EMAIL")
                    st.markdown(f":material/play_arrow: **Recommended Action:** `{action}`")
                    st.markdown(f"**Executive Summary:** {strategy.get('summary', 'N/A')}")
                    st.markdown(f"**Strategic Rationale:** {strategy.get('rationale', 'N/A')}")

                # Follow-Up Email Editor
                st.markdown("#### :material/edit: Grounded Follow-Up Draft (Human Review)")
                edit_subject = st.text_input(
                    "Subject Line:",
                    value=draft.get("subject", ""),
                    key="edit_subject_input"
                )
                edit_body = st.text_area(
                    "Email Content (Editable):",
                    value=draft.get("body", ""),
                    height=220,
                    key="edit_body_input"
                )

                if st.session_state.execution_phase == "AWAITING_APPROVAL":
                    # ✨ Instruct AI Copilot to Revise Draft
                    with st.expander(":material/auto_awesome: Instruct Copilot to Revise Draft / Tone", expanded=False):
                        st.caption("Tell the AI how you want to adjust the draft (e.g. 'Keep it under 75 words', 'Focus on ROI', 'Mention SOC-2 compliance').")
                        rev_c1, rev_c2 = st.columns([3, 1])
                        with rev_c1:
                            rev_instruction = st.text_input(
                                "Revision instruction:",
                                placeholder="e.g. Keep it concise, emphasize 15% annual discount, and ask for a 15-min call",
                                key="rev_input_field",
                                label_visibility="collapsed"
                            )
                        with rev_c2:
                            if st.button(":material/refresh: Re-draft", type="secondary", use_container_width=True):
                                if rev_instruction:
                                    with st.spinner("AI Copilot is revising follow-up draft..."):
                                        try:
                                            temp_state = state.copy()
                                            temp_state["user_request"] = rev_instruction
                                            updated_comm_state = run_async(communication_node(temp_state))
                                            if updated_comm_state.get("followup_draft"):
                                                st.session_state.workflow_state["followup_draft"] = updated_comm_state.get("followup_draft")
                                                st.success("Draft revised with your custom instruction!")
                                                st.rerun()
                                        except Exception as e:
                                            st.error(f"Failed to revise draft: {e}")

                    st.info(
                        ":material/warning: **Human Approval Required:** Review or edit the drafted follow-up above before executing the write to HubSpot CRM."
                    )

                    btn_c1, btn_c2 = st.columns(2)
                    with btn_c1:
                        if st.button(
                            ":material/check_circle: Approve & Write to HubSpot",
                            type="primary",
                        ):
                            with st.spinner("Executing approved CRM task and logging activity..."):
                                try:
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

                                    run_async(
                                        sales_graph.aupdate_state(
                                            config, update_payload, as_node="communication"
                                        )
                                    )
                                    final_result = run_async(
                                        sales_graph.ainvoke(None, config=config)
                                    )

                                    st.session_state.workflow_state = final_result
                                    st.session_state.execution_phase = "COMPLETED"
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Approval execution failed: {e}")

                    with btn_c2:
                        if st.button(":material/cancel: Reject / Skip Action"):
                            try:
                                config = {"configurable": {"thread_id": st.session_state.thread_id}}
                                run_async(
                                    sales_graph.aupdate_state(
                                        config,
                                        {"approval_status": "REJECTED"},
                                        as_node="communication",
                                    )
                                )
                                final_result = run_async(
                                    sales_graph.ainvoke(None, config=config)
                                )
                                st.session_state.workflow_state = final_result
                                st.session_state.execution_phase = "COMPLETED"
                                st.rerun()
                            except Exception as e:
                                st.error(f"Rejection failed: {e}")

                elif st.session_state.execution_phase == "COMPLETED":
                    action_res = state.get("action_result") or {}
                    verify_res = state.get("verification_result") or {}

                    if state.get("approval_status") in ("APPROVED", "MODIFIED"):
                        st.success(":material/check_circle: **Action Completed & Verified in HubSpot CRM!**")
                        with st.container(border=True):
                            r1, r2 = st.columns(2)
                            r1.metric("HubSpot Task ID", action_res.get("task_id", "N/A"))
                            r2.metric("HubSpot Note ID", action_res.get("note_id", "N/A"))
                            r3, r4 = st.columns(2)
                            r3.metric("Verification Status", verify_res.get("status", "N/A"))
                            r4.metric("CRM Verified", str(verify_res.get("verified", False)))
                            st.caption(f"Persisted to HubSpot CRM at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    else:
                        st.warning("Action was cancelled / rejected by user. No CRM writes were performed.")

    # -----------------------------------------------------------------------
    # Interactive AI Pipeline Diagnostician & Sales Copilot Chat
    # -----------------------------------------------------------------------
    st.divider()
    st.subheader(":material/forum: Interactive AI Pipeline Diagnostician & Sales Chat")
    st.caption("Chat with ClosePilot in real time. Ask strategic questions, analyze pipeline bottlenecks, compare opportunities, or diagnose stalled deals.")

    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = [
            {
                "role": "assistant",
                "content": "👋 Hi! I'm ClosePilot. Ask me anything about your active sales pipeline, deal blockers, or why specific opportunities were prioritized."
            }
        ]

    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_chat_input = st.chat_input("Chat with ClosePilot (e.g. 'Analyze my CRM pipeline', 'Why is Acme Corp prioritized?', 'Make draft shorter')...")
    if user_chat_input:
        st.session_state.chat_messages.append({"role": "user", "content": user_chat_input})
        input_lower = user_chat_input.lower().strip()

        # Check Intent 1: Pipeline Analysis / Follow-Up Generation
        is_analysis_intent = any(
            kw in input_lower for kw in [
                "analyze", "follow up", "followup", "who should i", "priority", "prioritize",
                "find deal", "find urgent", "enterprise deal", "stalled deal", "opportunities",
                "pipeline review", "run workflow", "which deal"
            ]
        )

        # Check Intent 2: Draft Revision
        is_revision_intent = any(
            kw in input_lower for kw in [
                "rewrite", "revise", "make it shorter", "make draft", "shorter", "change tone",
                "add discount", "friendlier", "more concise", "update draft", "re-draft", "mention"
            ]
        ) and st.session_state.workflow_state is not None

        if is_analysis_intent:
            with st.chat_message("user"):
                st.markdown(user_chat_input)

            with st.chat_message("assistant"):
                with st.spinner(f"ClosePilot is executing multi-agent pipeline for '{user_chat_input}'..."):
                    try:
                        config = {"configurable": {"thread_id": st.session_state.thread_id}}
                        initial_state = {
                            "thread_id": st.session_state.thread_id,
                            "user_request": user_chat_input,
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
                        opps = result.get("opportunities", [])
                        selected = result.get("selected_opportunity") or {}
                        
                        has_live_ids = any(str(d.get("id", "")).isdigit() for d in deals)
                        st.session_state.crm_source = "Live HubSpot" if has_live_ids else "Sandbox"
                        st.session_state.workflow_state = result
                        st.session_state.execution_phase = "AWAITING_APPROVAL"
                        
                        reply_text = f"✅ **Analysis Complete!** I evaluated **{len(deals)} active CRM deals**.\n\n🎯 **Top Priority:** **{selected.get('name', 'N/A')}** (${float(selected.get('amount', 0)):,.0f} • {selected.get('stage', 'N/A')})\n• **Score:** `{selected.get('score', 0):.0f} pts` ({', '.join(selected.get('score_reasons', [])[:2])})\n• **Key Contact:** {selected.get('contact_name')} ({selected.get('contact_title')})\n\n👉 *Review the strategic rationale and approve or customize the follow-up draft in the review panel above!*"
                        st.markdown(reply_text)
                        st.session_state.chat_messages.append({"role": "assistant", "content": reply_text})
                        st.rerun()
                    except Exception as e:
                        err_msg = f"Analysis workflow failed: {e}"
                        st.error(err_msg)
                        st.session_state.chat_messages.append({"role": "assistant", "content": err_msg})

        elif is_revision_intent:
            with st.chat_message("user"):
                st.markdown(user_chat_input)

            with st.chat_message("assistant"):
                with st.spinner("Revising follow-up email draft with your instructions..."):
                    try:
                        temp_state = st.session_state.workflow_state.copy()
                        temp_state["user_request"] = user_chat_input
                        updated_comm = run_async(communication_node(temp_state))
                        if updated_comm.get("followup_draft"):
                            st.session_state.workflow_state["followup_draft"] = updated_comm.get("followup_draft")
                            rev_draft = updated_comm.get("followup_draft")
                            reply_text = f"✨ **Draft Revised Successfully!**\n\n**Subject:** {rev_draft.get('subject')}\n\n```text\n{rev_draft.get('body')}\n```\n\n*The review card above has been updated. You can approve and write it to HubSpot whenever you are ready!*"
                            st.markdown(reply_text)
                            st.session_state.chat_messages.append({"role": "assistant", "content": reply_text})
                            st.rerun()
                    except Exception as e:
                        err_msg = f"Draft revision failed: {e}"
                        st.error(err_msg)
                        st.session_state.chat_messages.append({"role": "assistant", "content": err_msg})

        else:
            # General Conversational & Diagnostic Query
            with st.chat_message("user"):
                st.markdown(user_chat_input)

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
                        ai_reply = run_async(llm.generate(chat_system_prompt, user_chat_input))
                        st.markdown(ai_reply)
                        st.session_state.chat_messages.append({"role": "assistant", "content": ai_reply})
                    except Exception as e:
                        err_msg = f"Chat analysis error: {e}"
                        st.error(err_msg)
                        st.session_state.chat_messages.append({"role": "assistant", "content": err_msg})


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


# ===========================================================================
# TAB 5: SETTINGS & HEALTH CHECK
# ===========================================================================
with tab_settings:
    st.subheader(":material/settings: System Configuration & Integration Health")

    sett_c1, sett_c2 = st.columns(2)
    with sett_c1:
        with st.container(border=True):
            st.markdown("**LLM Configuration**")
            st.markdown(f"• Provider: `{current_settings.LLM_PROVIDER}`")
            st.markdown(f"• Model: `{current_settings.LLM_MODEL}`")
            st.markdown(f"• Groq API Key: `{'Configured' if current_settings.GROQ_API_KEY else 'Missing'}`")
            st.markdown(f"• NVIDIA NIM Key: `{'Configured' if current_settings.NVIDIA_API_KEY else 'Missing'}`")

    with sett_c2:
        with st.container(border=True):
            st.markdown("**HubSpot & Supabase Integration**")
            st.markdown(f"• HubSpot Client ID: `{current_settings.HUBSPOT_CLIENT_ID}`")
            st.markdown(f"• HubSpot Token: `{'Configured' if current_settings.HUBSPOT_ACCESS_TOKEN else 'Missing'}`")
            st.markdown(f"• Supabase URL: `{current_settings.SUPABASE_URL or 'Not configured'}`")
            st.markdown(f"• Backend Port: `{current_settings.BACKEND_PORT}`")

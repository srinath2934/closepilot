# ⚡ ClosePilot • AI Sales Follow-Up Copilot

> **Enterprise-Grade Autonomous CRM Investigation, Deterministic Opportunity Prioritization, Strategic Reasoning, and Human-in-the-Loop Execution.**

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://python.org)
[![LangGraph](https://img.shields.io/badge/Orchestrator-LangGraph-FF6F00?logo=langchain&logoColor=white)](https://github.com/langchain-ai/langgraph)
[![HubSpot MCP](https://img.shields.io/badge/Integration-HubSpot%20MCP-FF7A59?logo=hubspot&logoColor=white)](https://developers.hubspot.com/)
[![LLM Provider](https://img.shields.io/badge/LLM-Groq%20%7C%20NVIDIA%20NIM-F05032)](https://groq.com)
[![FastAPI](https://img.shields.io/badge/API-FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io)
[![Tests](https://img.shields.io/badge/Tests-14%2F14%20Passing-brightgreen?logo=pytest&logoColor=white)](https://pytest.org)

---

## 📑 Table of Contents
- [1. Executive Summary & Design Philosophy](#1-executive-summary--design-philosophy)
  - [1.1 What Makes a World-Class Production README?](#11-what-makes-a-world-class-production-readme)
- [2. Technology Stack & Architectural Rationale (Why We Chose It)](#2-technology-stack--architectural-rationale-why-we-chose-it)
- [3. The Business Problem](#3-the-business-problem)
- [4. The Proposed Solution](#4-the-proposed-solution)
- [5. High-Level System Architecture](#5-high-level-system-architecture)
- [6. Detailed Multi-Agent Workflow](#6-detailed-multi-agent-workflow)
- [7. Deterministic Prioritization Formula](#7-deterministic-prioritization-formula)
- [8. Safety, Guardrails & Zero-Hallucination Policy](#8-safety-guardrails--zero-hallucination-policy)
- [9. Repository File Structure](#9-repository-file-structure)
- [10. Getting Started & Installation](#10-getting-started--installation)
- [11. REST API Reference](#11-rest-api-reference)
- [12. Automated Testing & Verification](#12-automated-testing--verification)

---

## 1. Executive Summary & Design Philosophy

In enterprise B2B sales, account executives and founders manage dozens of simultaneous deals spread across complex sales cycles. High-value opportunities stall due to missing follow-ups, unclear buyer requirements, or lack of timely action after proposals are dispatched. 

**ClosePilot** is a production-grade stateful multi-agent sales copilot MVP designed as a real-world learning and reference architecture for building autonomous agent workflows. Engineered using **LangGraph**, **Model Context Protocol (MCP)**, and **NVIDIA / Groq LLMs**, it continuously audits live CRM pipelines (HubSpot), calculates deterministic urgency scores based on deal velocity and inactivity decay, generates context-grounded strategic outreach, and safely pauses at a **Human-in-the-Loop (HITL) gate** before executing verified CRM writes.

### 1.1 What Makes a World-Class Production README?

A great engineering README is not just a setup guide; it is the **technical single source of truth (SSOT)** for an entire system. In ClosePilot, our README follows seven core design principles:

1. **Clear Problem-Solution Pairing**: Immediately states the business value and how the architecture directly addresses real-world failure modes.
2. **Visual & Structural Digestibility**: Employs GitHub-native Mermaid flowcharts to communicate data flow, decision trees, and microservice topology in seconds.
3. **Rigorous Architectural Justification**: Explicitly documents *why* each technology was chosen over alternatives rather than listing libraries blindly.
4. **Deterministic Transparency**: Shares exact formulas, weights, and algorithms (e.g., our mathematical prioritization score) so behaviors are 100% predictable.
5. **Zero-Ambiguity Reproducibility**: Provides 1-command startup instructions, copy-pasteable environment templates, and Docker recipes that work on any machine on the first attempt.
6. **Complete API Contracts**: Details all REST endpoints, payloads, HTTP verbs, and interactive Swagger links.
7. **Verifiable Test Matrix**: Lists every unit, integration, and safety test case with automated execution commands to guarantee confidence before deployment.

---

## 2. Technology Stack & Architectural Rationale (Why We Chose It)

| Technology | Role in ClosePilot | Why We Chose It (Architectural Justification) | Alternatives Considered |
|---|---|---|---|
| **LangGraph** (v0.2+) | Multi-Agent Orchestration & Checkpointer State Machine | Provides cyclic state machines with **native checkpointer memory** and hard interrupts (`interrupt_before=["approval"]`). Crucial for Human-in-the-Loop safety gates where the workflow must pause, persist state across threads, and resume upon user action. | *CrewAI / AutoGen / LangChain Chains* — lack deterministic checkpointing and granular node-level state pauses. |
| **Model Context Protocol (MCP)** | CRM Tool Abstraction & Protocol Standardization | Decouples HubSpot CRM logic from LLM prompt engineering. Exposes standardized JSON-RPC schemas for tool execution, ensuring tool definitions can be audited, swapped, or extended to Salesforce/Pipedrive without rewriting agent logic. | *Raw REST SDK calls* — tightly couples prompt engineering to specific API schemas and lacks standardized discovery. |
| **NVIDIA NIM & Groq LPU** | Ultra-Fast Open LLM Inference (Llama 3.1 70B & 3.3 70B) | Delivers sub-second token generation, deterministic structured outputs, and enterprise compliance at a fraction of closed-source API costs with zero token rate-limit anxiety. | *OpenAI GPT-4o / Claude 3.5* — higher latency for real-time sales apps and proprietary vendor lock-in. |
| **FastAPI + Uvicorn** | High-Performance REST API Layer | Native asynchronous execution (`async`/`await`), automatic Pydantic request/response validation, and auto-generated interactive OpenAPI / Swagger docs at `/docs`. | *Flask / Django* — slower synchronous execution, heavier boilerplate, and manual documentation overhead. |
| **Streamlit** (v1.40+) | Enterprise Sales Dashboard | Allows rapid creation of reactive, multi-tab sales UIs with native session state management, custom CSS branding, and seamless Python integration without frontend build steps. | *React / Next.js* — requires separate build pipelines, TypeScript boilerplate, and backend-to-frontend synchronization complexity. |
| **Supabase PostgreSQL** | Persistence & Audit Event Log | Cloud PostgreSQL instance with Row-Level Security (RLS), ACID compliance, and relational schema for storing agent threads, execution runs, approval records, and immutable compliance audit logs. | *Local SQLite* — lacks multi-user cloud concurrency and production persistence. |
| **LangSmith** | Full-Stack Observability & Tracing | Real-time waterfall trace trees, latency diagnostics, token consumption breakdown, and step-by-step state inspection across every LangGraph node. | *Custom logging / MLflow* — lacks native out-of-the-box LangGraph state machine step visualization. |
| **Docker & Compose** | Containerization & Cloud Deployment | Packages both FastAPI and Streamlit into a lightweight `python:3.12-slim` container with health checks and 1-command startup (`docker compose up -d --build`). | *Bare-metal VM scripts* — prone to environment mismatch and dependency drift. |
| **uv Package Manager** | Modern Python Tooling | 10x-100x faster dependency resolution and deterministic virtual environments than standard `pip`. | *pip / poetry / conda* — slower install times and complex virtual environment conflicts. |

---

## 3. The Business Problem

Traditional sales workflows suffer from five fundamental breakdowns:

1. **Pipeline Blindspots & Inactivity Decay**: High-value enterprise deals often stall silently because sales reps lack automated, real-time alerts when high-intent opportunities (e.g. *Contract Sent*) go untouched for days.
2. **Context Fragmentation**: Deal values, stakeholder objections, and customer requirements are scattered across meeting notes, CRM history, and email threads.
3. **Generic, Impersonal Outreach**: Reps resort to generic templates that ignore specific buyer blockers (e.g., CFO milestone questions or custom SLA terms), reducing conversion rates.
4. **Autonomous AI Risk**: Purely autonomous agents can hallucinate discounts, fabricate non-existent meetings, or spam decision-makers with incorrect pricing.
5. **Inconsistent CRM Hygiene**: Even when follow-ups happen, reps frequently forget to log tasks and notes back into the CRM, breaking team visibility.

---

## 4. The Proposed Solution

The ClosePilot system solves these challenges through a **hybrid deterministic-reasoning architecture**:

```mermaid
flowchart TD
    A["🔍 1. Ingest Live Deals & Contacts (HubSpot MCP)"] --> B["📊 2. Compute Deterministic Urgency Score"]
    B --> C["🧠 3. Strategic Blocker Analysis (NVIDIA / Groq)"]
    C --> D["✍️ 4. Grounded Follow-up Email Draft"]
    D --> E{"🛡️ 5. Human Approval Gate"}
    
    E -->|Approved / Modified| F["⚡ 6. Execute CRM Task & Note (HubSpot)"]
    E -->|Rejected| G["⏭️ 6. Skip Write (Zero Side-Effects)"]
    
    F --> H["✅ 7. Read-After-Write Verification & Supabase Audit"]
```

* **Deterministic Prioritization**: Fast mathematical scoring rank-orders deals by stage weights, contract sizes, and days inactive without token consumption or hallucination.
* **Grounded LLM Reasoning**: Strategic analysis and zero-hallucination email drafting strictly constrained to verified CRM facts.
* **Human-in-the-Loop Gate**: The workflow hard-interrupts before any write operation, giving sales reps full authority to review, edit, approve, or reject outreach.
* **Read-After-Write Verification**: After write execution, the system queries the CRM to verify external state persistence.
* **Immutable Audit Trail**: Telemetry, approval decisions, and agent runs are logged into Supabase PostgreSQL for compliance.

---

## 5. High-Level System Architecture

```mermaid
flowchart TD
    subgraph UI ["🖥️ Presentation Layer"]
        STREAMLIT["Streamlit Sales Dashboard<br/>(closepilot-app.onrender.com)"]
        FASTAPI["FastAPI REST Server<br/>(closepilot-api.onrender.com)"]
    end

    subgraph Pipeline ["⚡ LangGraph Multi-Agent Pipeline"]
        N1["🔍 Research Node<br/>(HubSpot CRM Ingestion)"]
        N2["📊 Prioritize Node<br/>(Deterministic Scoring)"]
        N3["🧠 Strategy Node<br/>(Blocker Reasoning)"]
        N4["✍️ Communication Node<br/>(Email Drafting)"]
        N5{"🛡️ Approval Gate<br/>(HITL Pause)"}
        N6["⚡ Action Node<br/>(HubSpot Task/Note Write)"]
        N7["✅ Verification Node<br/>(Confirmation & Persistence)"]
    end

    subgraph Cloud ["🌐 Connected Services"]
        HUBSPOT["🔌 HubSpot Remote MCP"]
        LLM["🧠 NVIDIA NIM / Groq LPU"]
        SUPABASE[("🗄️ Supabase PostgreSQL")]
        LANGSMITH["📊 LangSmith Observability"]
    end

    STREAMLIT --> FASTAPI
    FASTAPI --> N1
    N1 --> N2
    N2 --> N3
    N3 --> N4
    N4 --> N5
    N5 -->|Approved| N6
    N6 --> N7

    N1 --> HUBSPOT
    N3 --> LLM
    N4 --> LLM
    N6 --> HUBSPOT
    N7 --> HUBSPOT
    N7 --> SUPABASE
    FASTAPI --> LANGSMITH
```

---

## 6. Detailed Multi-Agent Workflow

| Node / Agent | Responsibility | Implementation File |
|---|---|---|
| **1. Research Agent** | Connects to HubSpot MCP to ingest deals, contact associations, modification timestamps, and CRM notes. | [`app/graph/nodes/research.py`](file:///d:/sales%20agent/app/graph/nodes/research.py) |
| **2. Prioritization Engine** | Computes mathematical priority scores; matches custom prompt query intent and entities. | [`app/graph/nodes/prioritize.py`](file:///d:/sales%20agent/app/graph/nodes/prioritize.py) |
| **3. Strategy Agent** | Analyzes deal blockers, buyer persona drivers (CXO vs. Director), and determines optimal next actions. | [`app/graph/nodes/strategy.py`](file:///d:/sales%20agent/app/graph/nodes/strategy.py) |
| **4. Communication Drafter** | Drafts personalized, factual follow-up emails adhering to strict anti-invention guardrails. | [`app/graph/nodes/communication.py`](file:///d:/sales%20agent/app/graph/nodes/communication.py) |
| **5. Human Approval Gate** | LangGraph checkpointer pause point (`interrupt_before=["approval"]`) for human review. | [`app/graph/nodes/approval.py`](file:///d:/sales%20agent/app/graph/nodes/approval.py) |
| **6. Action Agent** | Executes approved write operations (creates HubSpot tasks and engagement notes). | [`app/graph/nodes/action.py`](file:///d:/sales%20agent/app/graph/nodes/action.py) |
| **7. Verification Agent** | Performs read-after-write verification to confirm CRM object existence and status. | [`app/graph/nodes/verification.py`](file:///d:/sales%20agent/app/graph/nodes/verification.py) |

---

## 7. Deterministic Prioritization Formula

The Prioritization Engine computes priority urgency without LLM variance:

$$\text{Priority Score} = S_{\text{stage}} + V_{\text{amount}} + I_{\text{inactivity}} - P_{\text{task}} - P_{\text{recent}} + B_{\text{query}}$$

### Scoring Parameters:
* **Stage Weights ($S_{\text{stage}}$)**:
  * Contract Sent: $+35\text{ pts}$
  * Decision Maker Bought-In: $+30\text{ pts}$
  * Proposal Submitted: $+25\text{ pts}$
  * Qualified to Buy: $+15\text{ pts}$
  * Presentation Scheduled: $+10\text{ pts}$
* **Deal Value ($V_{\text{amount}}$)**:
  * $\ge \$50,000$ (Tier-1 Enterprise): $+30\text{ pts}$
  * $\$20,000 - \$49,999$ (Mid-Market): $+20\text{ pts}$
  * $\$10,000 - \$19,999$ (Qualified): $+10\text{ pts}$
* **Inactivity Urgency ($I_{\text{inactivity}}$)**:
  * For $\text{days} \ge 3$: $\min(\text{days} \times 5, 30)\text{ pts}$
* **Safety Penalties**:
  * Existing scheduled task ($P_{\text{task}}$): $-40\text{ pts}$
  * Contacted within last 48 hours ($P_{\text{recent}}$): $-50\text{ pts}$
* **Prompt Query Match ($B_{\text{query}}$)**:
  * Exact match on company/contact/deal name in user prompt: $+100\text{ pts}$
  * Stage keyword match: $+40\text{ pts}$

---

## 8. Safety, Guardrails & Zero-Hallucination Policy

The system enforces enterprise AI safety standards:

1. **Anti-Invention Guardrails**:
   * Prompts explicitly prohibit hallucinating unapproved discounts, unauthorized pricing, or phantom meetings.
2. **Deterministic Hard Boundary**:
   * Deal ranking and prioritization are computed in deterministic Python code rather than LLM guessing.
3. **No Unattended CRM Writes**:
   * No tool or agent has autonomous write privileges without passing through the Human Approval Gate.
4. **Graceful Degradation / Circuit Breaker**:
   * If live HubSpot OAuth tokens expire, the system smoothly falls back to sandbox data with clear UI warnings rather than crashing.

---

## 9. Repository File Structure

```
d:/sales agent/
├── app/
│   ├── config/              # Centralized environment configuration (Pydantic Settings)
│   │   └── settings.py      # Dynamic .env reload, multi-provider configuration
│   ├── llm/                 # Unified LLM Provider Interface
│   │   └── provider.py      # Groq LPU, NVIDIA NIM, OpenAI, and Mock providers
│   ├── mcp/                 # Model Context Protocol Tools Layer
│   │   ├── client.py        # Base MCP tool execution interface
│   │   └── hubspot.py       # Live HubSpot REST/MCP client with PKCE OAuth & sandbox
│   ├── graph/               # LangGraph Stateful Agent Workflow
│   │   ├── state.py         # Type-safe SalesState schema
│   │   ├── graph.py         # StateGraph with checkpointer & interrupt_before=["approval"]
│   │   └── nodes/           # Single-responsibility agent nodes
│   │       ├── research.py  # Ingests deals, contacts, notes from HubSpot
│   │       ├── prioritize.py# Deterministic scoring engine + query matching
│   │       ├── strategy.py  # Chain-of-thought sales strategy reasoning
│   │       ├── communication.py # Zero-hallucination email drafter
│   │       ├── approval.py  # Human approval pause gate
│   │       ├── action.py    # HubSpot task & note write executor
│   │       └── verification.py # Read-after-write confirmation
│   ├── prompts/             # Guardrailed Prompt Engineering
│   │   ├── strategy_prompts.py
│   │   └── communication_prompts.py
│   ├── database/            # Persistence & Compliance Audit Trail
│   │   ├── connection.py    # Supabase PostgREST async client with circuit breaker
│   │   └── repositories/    # Audit, Approval, and Run telemetry repositories
│   └── main.py              # FastAPI REST API (PKCE OAuth, Health, Workflow Lifecycle)
├── frontend/
│   └── app.py               # Streamlit Enterprise Multi-Tab Dashboard
├── scripts/
│   └── seed_crm.py          # Direct CRM deal & contact seeding script
├── tests/
│   ├── unit/                # Scoring algorithm & repository unit tests
│   └── integration/         # API, graph lifecycle & multi-scenario integration tests
├── run_demo.py              # Standalone CLI validation runner
└── requirements.txt         # Pinned production dependencies
```

---

## 10. Getting Started & Installation

### Prerequisites
* Python 3.11+
* [uv](https://github.com/astral-sh/uv) (recommended) or standard `pip`
* HubSpot Developer Account (optional for live mode; mock mode works out of the box)
* Groq API Key or NVIDIA NIM API Key

### Step 1: Clone and Install Dependencies
```bash
# Using uv (fastest)
uv sync

# Or using standard pip
pip install -r requirements.txt
```

### Step 2: Configure Environment Variables
Create a `.env` file in the project root:
```env
# LLM Provider: groq | nvidia | openai | mock
LLM_PROVIDER=nvidia
LLM_MODEL=meta/llama-3.1-70b-instruct
NVIDIA_API_KEY=your_nvidia_api_key

# HubSpot Integration
HUBSPOT_APP_ID=your_hubspot_app_id
HUBSPOT_CLIENT_ID=your_hubspot_client_id
HUBSPOT_CLIENT_SECRET=your_hubspot_client_secret
HUBSPOT_ACCESS_TOKEN=your_access_token_here
HUBSPOT_USE_MOCK=false

# Supabase Persistence (Optional)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_publishable_key

# Backend Server
BACKEND_HOST=127.0.0.1
BACKEND_PORT=8000
```

### Step 3: Run the Backend & Streamlit Dashboard

**Terminal 1 — FastAPI Backend:**
```bash
uv run uvicorn app.main:app --port 8000 --reload
```

**Terminal 2 — Streamlit Dashboard:**
```bash
uv run streamlit run frontend/app.py --server.port 8501
```

Open **`http://localhost:8501`** in your browser.

---

### 🐳 Run with Docker (1-Command Launch)
Prefer running everything in an isolated container? Use the unified Docker setup:

```bash
docker compose up -d --build
```
* Access UI: `http://localhost:8501`
* Access API & Docs: `http://localhost:8000/docs`

👉 *For full container management, ECS, Cloud Run, and reverse proxy recipes, see the **[Docker Deployment Guide (DOCKER_README.md)](file:///d:/sales%20agent/DOCKER_README.md)**.*

---

## 11. REST API Reference

The FastAPI backend runs on `http://127.0.0.1:8000` with interactive Swagger docs at `/docs`:

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Service health and active MCP/LLM mode summary. |
| `GET` | `/api/health` | Comprehensive connection diagnostics for HubSpot & Supabase. |
| `GET` | `/api/settings` | Current configuration details (redacted keys). |
| `GET` | `/api/deals` | Ingests all active raw deals from HubSpot CRM. |
| `POST`| `/api/deals/seed` | Dynamically creates a new deal in HubSpot CRM. |
| `POST`| `/api/workflow/start` | Initiates LangGraph agent run; executes through Research $\rightarrow$ Prioritize $\rightarrow$ Strategy $\rightarrow$ Communication, then pauses at Human Approval. |
| `POST`| `/api/workflow/approve` | Submits human approval/modifications and resumes execution through Action $\rightarrow$ Verification $\rightarrow$ END. |
| `GET` | `/api/workflow/status/{thread_id}` | Retrieves full checkpoint state for an active workflow thread. |
| `GET` | `/oauth/login` | Initiates HubSpot PKCE OAuth authorization. |
| `GET` | `/oauth/callback` | Exchanges authorization code for live HubSpot access token. |

---

## 12. Automated Testing & Verification

The test suite covers unit logic, repository persistence, API lifecycle, and end-to-end multi-scenario agent flows:

```bash
uv run pytest tests/ -v
```

### Verified Test Matrix (14/14 Passing):
* ✅ `test_api_root` — Root endpoint sanity
* ✅ `test_api_deals` — Live deals retrieval
* ✅ `test_api_workflow_lifecycle` — Complete start $\rightarrow$ approve $\rightarrow$ complete REST lifecycle
* ✅ `test_end_to_end_graph_execution` — LangGraph checkpointer pause and resume
* ✅ `test_scenario_1_standard_flow` — End-to-end standard sales inquiry
* ✅ `test_scenario_2_custom_prompt_targeting` — Prompt entity matching & $+100\text{ pt}$ score boost
* ✅ `test_scenario_3_deal_switching_synchronization` — UI opportunity switcher checkpointer synchronization
* ✅ `test_scenario_4_rejection_safety` — Rejection handling without write execution
* ✅ `test_scenario_5_human_draft_modification` — Custom subject/body preservation on write
* ✅ `test_runs_repository` — Thread & telemetry logging
* ✅ `test_audit_repository` — Event-level audit logging
* ✅ `test_high_value_contract_sent_scoring` — Mathematical scoring verification
* ✅ `test_recent_contact_penalty` — $-50\text{ pt}$ penalty for recent touchpoints
* ✅ `test_future_task_penalty` — $-40\text{ pt}$ penalty for existing scheduled tasks

---

### Standalone CLI Execution
Run the standalone end-to-end execution script anytime without browser overhead:
```bash
uv run python run_demo.py
```

---
 
*A real-world Production AI Agent MVP & Educational Reference Architecture for Autonomous Sales Engineering.*


FINAL TECHNICAL ARCHITECTUREAI Sales Intelligence & Follow-Up Agent

GWC Data.AI — Final Architecture Baseline

LangGraph • MCP • HubSpot • Gmail • NVIDIA NIM • Supabase PostgreSQL + pgvector

# 1. Architecture Decision

The system will be implemented as a stateful hierarchical agentic workflow. LangGraph is the orchestration layer; specialized agents handle research, strategy and communication; deterministic application logic handles opportunity prioritization; MCP provides standardized external tool access; HubSpot remains the CRM system of record; Gmail is the communication system; and Supabase PostgreSQL with pgvector provides application persistence and semantic memory.

# 2. Final Architecture

USER / SALES REPRESENTATIVE        |        v+-----------------------------+| Web Application              || Streamlit / React            |+--------------+--------------+               |               v+-----------------------------+| FastAPI                      || API / Auth / Streaming       |+--------------+--------------+               |               v+==============================================================+|                         LANGGRAPH                            ||                    AGENT ORCHESTRATION                       ||                                                              ||  +------------------+                                        ||  | Orchestrator     |                                        ||  | / Router         |                                        ||  +--------+---------+                                        ||           |                                                  ||     +-----+---------+----------------+                       ||     |               |                |                       ||     v               v                v                       ||  Research       Strategy       Communication                ||    Agent          Agent             Agent                    ||     |               |                |                       ||     +---------------+----------------+                       ||                     |                                        ||                     v                                        ||              HUMAN APPROVAL                                  ||                /        \                                    ||           REJECT        APPROVE                              ||             |              |                                  ||             v              v                                  ||            END          ACTION                                ||                           |                                   ||                           v                                   ||                       VERIFY                                 ||                       /    \                                  ||                  SUCCESS   FAILURE                            ||                     |        |                               ||                     v        v                               ||                    END   BOUNDED RETRY                        |+=========================+====================================+                          |                          v                 +------------------+                 |   TOOL / DATA    |                 |      LAYER       |                 +--------+---------+                          |           +--------------+---------------+           |              |               |           v              v               v     HubSpot MCP     Gmail MCP/API    pgvector           |              |               |           v              v               v       HubSpot          Gmail       Semantic Memory          CRM                         / History                          |                          v                +----------------------+                | Supabase PostgreSQL  |                |                      |                | Agent threads        |                | Agent runs           |                | Approvals            |                | Audit events         |                | Embeddings metadata  |                +----------------------+

# 3. Core Workflow

READ → REASON → PROPOSE → APPROVE → ACT → VERIFY → AUDIT

User asks a sales question or requests follow-up handling.

FastAPI creates or loads a LangGraph thread.

Orchestrator determines the required workflow.

Research Agent retrieves relevant HubSpot CRM data through MCP.

Semantic retrieval retrieves historical email/meeting/call context when required.

Deterministic prioritization scores opportunities.

Strategy Agent decides the recommended next action.

Communication Agent generates a grounded follow-up.

LangGraph interrupts and waits for human approval.

Action node executes the approved CRM/email action.

Verification node checks the external system.

Run, approval and audit information are persisted.

User receives the final verified result.

# 4. Agent Responsibilities

Component

Responsibility

Access

Orchestrator

Controls workflow, state and routing.

LangGraph state

Research Agent

Retrieves deals, contacts, companies, activities and tasks.

HubSpot MCP read

Prioritization

Calculates explainable follow-up priority.

Deterministic application logic

Strategy Agent

Determines why the opportunity needs attention and recommends the next action.

CRM + semantic context

Communication Agent

Generates a personalized, evidence-grounded message.

Retrieved context

Human Approval

Reviews, edits, approves or rejects the proposed write action.

UI + LangGraph interrupt

Action Node

Executes only an approved external action.

HubSpot/Gmail write capability

Verification Node

Confirms the external action actually succeeded.

External-system read

# 5. LLM Layer

Primary LLM: NVIDIA NIM/API Catalog, provided the required model and current development access are available. Fallback: Groq. The application should expose an internal model interface so the provider can be changed through configuration.

The LLM is responsible for reasoning, planning, tool selection and language generation.

The LLM should NOT be responsible for deterministic opportunity scoring or directly bypassing approval controls.

# 6. LangGraph Layer

Recommended graph:

START → Intent Router → Research → Prioritize → Strategy → Communication → Human Approval → Action → Verification → END

Conditional branches:

No relevant opportunity → report and end.

Approval rejected → end without external write.

Action failure → bounded retry or human escalation.

Verification failure → report failure/inconsistency rather than claiming success.

# 7. MCP Layer

MCP is the tool-connectivity layer, not the agent. LangGraph and the agents determine what should be done; MCP exposes external capabilities in a standardized way.

HubSpot: use the official HubSpot Remote MCP server for CRM context and actions.

Reference: https://developers.hubspot.com/ai-tools/mcp

Gmail: use Gmail MCP for supported retrieval/draft capabilities. If direct sending is unavailable in the connected Gmail MCP environment, use a controlled Gmail API action for the final approved send.

Reference: https://developers.google.com/workspace/gmail/api/reference/mcp

Implementation rule: inspect the actual tools exposed by each MCP server. Never invent or hard-code undocumented tool names.

# 8. Data Architecture

System

Stores

Role

HubSpot

Contacts, companies, deals, activities, tasks

CRM system of record

Gmail

Email threads and messages

Communication source

Supabase PostgreSQL

Agent state, runs, approvals, audit events

Application persistence

pgvector

Embeddings and semantic memory records

Semantic retrieval

# 9. Why pgvector?

pgvector is used only for unstructured information where semantic retrieval is useful. It should not replace normal HubSpot queries for structured CRM fields.

Use pgvector for

Do not use pgvector for

Emails, meeting notes, call notes, customer requirements, proposal discussions, historical conversations

Deal amount, deal stage, contact ID, company ID, dates, tasks and other structured CRM fields

# 10. Database Schema — Initial

Table

Initial fields

agent_threads

thread_id, user_id, status, created_at, updated_at

agent_runs

run_id, thread_id, provider, model, status, started_at, completed_at, error

approval_requests

approval_id, run_id, action_type, target_id, proposed_content, status, approved_at

audit_events

event_id, run_id, node, tool, action, status, timestamp, metadata

conversation_embeddings

id, source_type, source_id, content, embedding, metadata, created_at

HubSpot data should not be fully duplicated into this database. HubSpot remains the CRM source of truth.

# 11. Technology Stack

Layer

Technology

Purpose

Programming

Python

Application and AI development

LLM

NVIDIA NIM

Primary reasoning and generation

LLM fallback

Groq

Fallback inference provider

Agent orchestration

LangGraph

State, routing, HITL and recovery

CRM

HubSpot

Real CRM

CRM integration

HubSpot Remote MCP

Agent-to-CRM tool access

Email

Gmail MCP / Gmail API

Email retrieval and approved actions

Backend

FastAPI

API and integration layer

Frontend MVP

Streamlit

Fast approval/demo UI

Database

PostgreSQL via Supabase

Application persistence

Vector search

pgvector

Semantic memory

Embeddings

Open embedding model

Embedding generation

Container

Docker

Reproducible runtime

Source control

Git + GitHub

Versioning

Deployment

Render initially

Demo hosting

Testing

pytest

Automated tests

Observability

Structured logs; LangSmith optional

Agent tracing and debugging

# 12. Security Boundary

The agent must not have unrestricted write authority. Read operations can be automated within the connected user's permissions. Write operations follow: propose → human approval → execute → verify.

Least-privilege OAuth scopes.

Secrets only in environment variables/platform secret storage.

No credentials in GitHub.

Verify target contact/deal before action.

Record approval and execution audit events.

Bounded retries only.

Never expose tokens in logs.

# 13. Opportunity Prioritization

Use deterministic scoring first:

Deal value → positive weight.

Proposal/negotiation stage → positive weight.

Days since last activity → positive weight.

Explicit customer request awaiting response → strong positive weight.

Existing future follow-up task → negative weight.

Very recent contact → negative weight.

The LLM explains the score using retrieved evidence; it does not invent the underlying score.

# 14. Evaluation

CRM retrieval accuracy.

Follow-up prioritization accuracy.

Grounding / hallucination rate.

Correct tool selection.

Approval enforcement.

Successful external-action rate.

Verification accuracy.

Failure recovery behavior.

End-to-end task completion.

Latency and number of LLM calls.

# 15. MVP Scope

Priority

Feature

Status target

P0

HubSpot OAuth + Remote MCP

Must work

P0

LangGraph state and workflow

Must work

P0

Research Agent

Must work

P0

Opportunity prioritization

Must work

P0

Strategy Agent

Must work

P0

Communication Agent

Must work

P0

Human approval interrupt

Must work

P0

Approved HubSpot/Gmail action

Must work

P0

Verification

Must work

P1

Supabase persistence

Add after core path

P1

pgvector semantic memory

Add if time permits

P1

Minimal Streamlit UI

Add after core path

P2

Deployment polish / advanced analytics

Only after working demo

# 16. What We Are Explicitly NOT Building

Uncontrolled agent swarm.

Separate Redis + MongoDB + Pinecone + PostgreSQL stack.

Kubernetes.

Kafka.

Fine-tuning.

Large RAG system before CRM retrieval works.

Autonomous mass-email campaign.

Unapproved email sending.

Complex ML lead-scoring model for the first version.

Synthetic-only CRM demo.

# 17. Final Engineering Principle

READ → REASON → PROPOSE → APPROVE → ACT → VERIFY → AUDIT

This is the central design principle of the project. It gives the system real agentic behavior while maintaining control over external business actions.

# 18. Implementation Order

Create Git repository and Python environment.

Configure HubSpot OAuth and Remote MCP.

Perform the first real HubSpot read operation.

Create LangGraph state and graph skeleton.

Implement Research Agent.

Implement deterministic prioritization.

Implement Strategy Agent.

Implement Communication Agent.

Implement human approval interrupt.

Implement approved external action.

Implement verification.

Persist runs, approvals and audit events in Supabase.

Add pgvector semantic retrieval.

Build minimal Streamlit UI.

Deploy only after the complete vertical slice works.

Document setup, architecture, security, limitations and demo steps.

# 19. Final Stack — Locked Baseline

Python + FastAPI + LangGraph + NVIDIA NIM + HubSpot Remote MCP + Gmail MCP/API + Supabase PostgreSQL + pgvector + Streamlit + Docker + GitHub

# 20. Reference Documentation

HubSpot Remote MCP: https://developers.hubspot.com/ai-tools/mcp

Gmail MCP: https://developers.google.com/workspace/gmail/api/reference/mcp

LangGraph: https://docs.langchain.com/oss/python/langgraph

Supabase: https://supabase.com/

Supabase pgvector: https://supabase.com/docs/guides/database/extensions/pgvector

NVIDIA NIM: https://docs.nvidia.com/nim/

Render: https://render.com/docs/free

| Component | Responsibility | Access |

| --- | --- | --- |

| Orchestrator | Controls workflow, state and routing. | LangGraph state |

| Research Agent | Retrieves deals, contacts, companies, activities and tasks. | HubSpot MCP read |

| Prioritization | Calculates explainable follow-up priority. | Deterministic application logic |

| Strategy Agent | Determines why the opportunity needs attention and recommends the next action. | CRM + semantic context |

| Communication Agent | Generates a personalized, evidence-grounded message. | Retrieved context |

| Human Approval | Reviews, edits, approves or rejects the proposed write action. | UI + LangGraph interrupt |

| Action Node | Executes only an approved external action. | HubSpot/Gmail write capability |

| Verification Node | Confirms the external action actually succeeded. | External-system read |

| System | Stores | Role |

| --- | --- | --- |

| HubSpot | Contacts, companies, deals, activities, tasks | CRM system of record |

| Gmail | Email threads and messages | Communication source |

| Supabase PostgreSQL | Agent state, runs, approvals, audit events | Application persistence |

| pgvector | Embeddings and semantic memory records | Semantic retrieval |

| Use pgvector for | Do not use pgvector for |

| --- | --- |

| Emails, meeting notes, call notes, customer requirements, proposal discussions, historical conversations | Deal amount, deal stage, contact ID, company ID, dates, tasks and other structured CRM fields |

| Table | Initial fields |

| --- | --- |

| agent_threads | thread_id, user_id, status, created_at, updated_at |

| agent_runs | run_id, thread_id, provider, model, status, started_at, completed_at, error |

| approval_requests | approval_id, run_id, action_type, target_id, proposed_content, status, approved_at |

| audit_events | event_id, run_id, node, tool, action, status, timestamp, metadata |

| conversation_embeddings | id, source_type, source_id, content, embedding, metadata, created_at |

| Layer | Technology | Purpose |

| --- | --- | --- |

| Programming | Python | Application and AI development |

| LLM | NVIDIA NIM | Primary reasoning and generation |

| LLM fallback | Groq | Fallback inference provider |

| Agent orchestration | LangGraph | State, routing, HITL and recovery |

| CRM | HubSpot | Real CRM |

| CRM integration | HubSpot Remote MCP | Agent-to-CRM tool access |

| Email | Gmail MCP / Gmail API | Email retrieval and approved actions |

| Backend | FastAPI | API and integration layer |

| Frontend MVP | Streamlit | Fast approval/demo UI |

| Database | PostgreSQL via Supabase | Application persistence |

| Vector search | pgvector | Semantic memory |

| Embeddings | Open embedding model | Embedding generation |

| Container | Docker | Reproducible runtime |

| Source control | Git + GitHub | Versioning |

| Deployment | Render initially | Demo hosting |

| Testing | pytest | Automated tests |

| Observability | Structured logs; LangSmith optional | Agent tracing and debugging |

| Priority | Feature | Status target |

| --- | --- | --- |

| P0 | HubSpot OAuth + Remote MCP | Must work |

| P0 | LangGraph state and workflow | Must work |

| P0 | Research Agent | Must work |

| P0 | Opportunity prioritization | Must work |

| P0 | Strategy Agent | Must work |

| P0 | Communication Agent | Must work |

| P0 | Human approval interrupt | Must work |

| P0 | Approved HubSpot/Gmail action | Must work |

| P0 | Verification | Must work |

| P1 | Supabase persistence | Add after core path |

| P1 | pgvector semantic memory | Add if time permits |

| P1 | Minimal Streamlit UI | Add after core path |

| P2 | Deployment polish / advanced analytics | Only after working demo |
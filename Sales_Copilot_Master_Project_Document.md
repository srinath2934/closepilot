MASTER PROJECT DOCUMENTAI Sales Intelligence & Follow-Up Agent

LangGraph • MCP • HubSpot • Gmail • NVIDIA NIM • PostgreSQL + pgvector

GWC Data.AI — 45-Day Project Concept / One-Day MVP Baseline

# 1. Executive Summary

The proposed system is a real, end-to-end AI Sales Intelligence & Follow-Up Agent. It connects to a real HubSpot CRM and email environment, uses LangGraph to orchestrate stateful agent workflows, uses MCP to access external business tools, uses an LLM for reasoning and communication generation, and uses PostgreSQL with pgvector for application persistence and semantic sales memory.

The system is designed around a controlled workflow: discover opportunities → retrieve context → prioritize → reason about the next action → generate a personalized follow-up → obtain human approval → execute the approved action → verify the result → record an audit trail.

# 2. Business Problem

Sales representatives must manually inspect CRM records to identify overdue or high-value follow-ups.

Important customer context can be distributed across deals, activities, emails, notes and previous conversations.

Generic follow-up messages reduce personalization and may ignore the customer's actual previous request.

Sales actions may be performed without consistent CRM logging.

Fully autonomous CRM actions can be risky because an AI system may select the wrong contact, deal or message.

# 3. Proposed Solution

Build a hierarchical sales agent that combines structured CRM retrieval, semantic conversation retrieval, LLM reasoning, controlled tool execution and human approval.

Primary user request:

"Who should I follow up with today, why, and what should I send?"

# 4. Core End-to-End Workflow

User submits a sales request.

LangGraph loads or creates the workflow state.

Research Agent retrieves relevant HubSpot CRM information through MCP.

The system optionally retrieves historical email/meeting/call context using semantic search.

Prioritization logic ranks opportunities using explainable business rules.

Strategy Agent determines why the opportunity needs attention and recommends the next action.

Communication Agent generates a personalized follow-up grounded in retrieved evidence.

LangGraph pauses for explicit human approval before a write action.

Action Agent executes the approved CRM/email action through the permitted integration.

Verification Agent checks the resulting external state.

The system stores the run, approval, action and verification result in the application database.

The UI reports the final result.

# 5. High-Level Architecture

Logical architecture:

User → Streamlit/React → FastAPI → LangGraph Orchestrator

LangGraph → Research / Strategy / Communication / Action / Verification nodes

Agent tools → MCP Client → HubSpot Remote MCP and Gmail MCP where supported

Semantic retrieval → PostgreSQL + pgvector

Application persistence → Supabase PostgreSQL

LLM reasoning → NVIDIA NIM as primary provider, with a provider abstraction/fallback if required

# 6. Agent Architecture

Component

Responsibility

Data / Access

Orchestrator

Routes the workflow and controls state transitions.

LangGraph state

Research Agent

Finds relevant deals, contacts, activities and tasks.

HubSpot MCP read access

Prioritization

Computes explainable opportunity priority.

Structured CRM evidence

Strategy Agent

Determines recommended next sales action.

CRM + semantic context

Communication Agent

Generates a grounded personalized follow-up.

Retrieved evidence

Human Approval

Allows review, edit, approve or reject.

UI + LangGraph interrupt

Action Agent

Executes only the approved external action.

HubSpot/Gmail write capability

Verification Agent

Checks whether the external action succeeded.

External-system read access

# 7. LangGraph Workflow

Recommended graph:

START → Intent Router → Research → Prioritize → Strategy → Communication → Human Approval → Action → Verification → END

Conditional branches:

Unsupported/irrelevant request → controlled response/end.

No suitable opportunity → report no follow-up required.

Approval rejected → end without write action.

Action failure → bounded retry or human escalation.

Verification failure → report inconsistency and do not claim success.

# 8. LangGraph State

Initial state fields:

thread_id

user_request

intent

deals

contacts

activities

tasks

semantic_context

opportunities

selected_opportunity

priority_score

strategy

followup_draft

approval_status

approved_action

action_result

verification_result

errors

retry_count

# 9. MCP Architecture

MCP is the tool-access boundary, not the agent itself. The LLM/LangGraph workflow decides what needs to be done; MCP provides standardized access to external capabilities.

Primary integration: HubSpot Remote MCP. HubSpot documents its Remote MCP server as a way for MCP-compatible AI tools/agents to access CRM context and actions according to the connected user's permissions.

HubSpot MCP reference: https://developers.hubspot.com/ai-tools/mcp

Email integration: use Gmail MCP where its available toolset satisfies the requirement. Google's current official Gmail MCP documentation emphasizes search/retrieval and draft creation; if direct sending is unavailable in the connected environment, use a controlled Gmail API action for the final approved send.

Gmail MCP reference: https://developers.google.com/workspace/gmail/api/reference/mcp

Implementation rule: inspect the actual tools exposed by each MCP server at runtime. Do not invent or assume tool names.

# 10. Database Architecture

Use one primary application database: PostgreSQL, hosted through Supabase. Enable pgvector in the same PostgreSQL database for semantic retrieval. Do not add Pinecone, MongoDB, Redis or Chroma unless a measured requirement appears.

System

Owns

Access

HubSpot

Contacts, companies, deals, CRM activities and tasks

HubSpot MCP

Gmail

Email threads and mailbox data

Gmail MCP/API

PostgreSQL/Supabase

Application state, approvals, audit and run metadata

Direct application DB

pgvector

Embeddings and semantic sales-memory records

Vector similarity queries

# 11. Recommended Database Tables

agent_threads: thread_id, user_id, status, created_at, updated_at

agent_runs: run_id, thread_id, model_provider, status, started_at, completed_at, error

approval_requests: approval_id, run_id, action_type, target_id, proposed_content, status, approved_at

audit_events: event_id, run_id, node, tool, action, status, timestamp, metadata

conversation_embeddings: id, source_type, source_id, content, embedding, metadata, created_at

Do not replicate the entire HubSpot CRM into PostgreSQL. HubSpot remains the CRM system of record.

# 12. Vector Database / Semantic Memory

A vector database is useful only for unstructured information that benefits from semantic search. Structured CRM fields should continue to be queried from HubSpot.

Use pgvector for

Do not use pgvector for

Emails, meeting notes, call notes, customer requirements, proposal discussions, historical conversations

Deal amount, deal stage, contact ID, company ID, dates, tasks and other structured CRM fields

# 13. Technology Stack

Layer

Technology

Purpose

Selection reason

Language

Python

Application and AI development

Strong AI, API and data ecosystem

LLM

NVIDIA NIM / API Catalog

Reasoning, planning and generation

Suitable primary inference option; provider abstraction retained

LLM fallback

Groq

Fallback inference

Fast hosted inference option

Orchestration

LangGraph

Stateful graph, routing, HITL and recovery

Matches multi-step workflow requirements

CRM

HubSpot

Real sales system of record

Direct business relevance

CRM integration

HubSpot Remote MCP

Agent tool access

Official MCP integration

Email

Gmail MCP / Gmail API

Conversation retrieval and approved sending

Real communication channel

Backend

FastAPI

Application API and integration layer

Fast Python implementation

Frontend

Streamlit

MVP interface and approval screen

Fastest implementation; replace with React later if needed

Database

PostgreSQL via Supabase

Application persistence

Hosted relational DB with free development tier

Vector search

pgvector

Semantic sales memory

Vector search inside PostgreSQL

Embeddings

Open embedding model

Create vectors for unstructured sales content

Avoid vendor lock-in

Container

Docker

Reproducible runtime

Standard deployment artifact

Source control

Git + GitHub

Versioning and portfolio

Standard engineering workflow

Deployment

Render initially

Public demo

Simple deployment; document free-tier limitations

Testing

pytest

Unit/integration tests

Standard Python testing

Observability

Structured logs; LangSmith optional

Trace agent execution

Start simple, add tracing if time permits

# 14. Security and Governance

Use least-privilege OAuth scopes for HubSpot and Gmail.

Store secrets only in environment variables or platform secret managers.

Never commit .env files or access tokens.

Separate read operations from write operations in the application design.

Require explicit human approval before sending/logging follow-up communications or modifying CRM records.

Verify the target contact/deal before executing an approved action.

Record approval and execution events in the audit table.

Use bounded retries and human escalation for repeated failures.

Do not log raw OAuth tokens or sensitive email contents unnecessarily.

# 15. Functional Requirements

ID

Requirement

FR-01

Accept natural-language sales requests.

FR-02

Identify the requested sales workflow.

FR-03

Retrieve relevant HubSpot CRM context.

FR-04

Retrieve relevant historical communication context when needed.

FR-05

Rank follow-up opportunities with explainable rules.

FR-06

Explain why an opportunity is prioritized.

FR-07

Generate a personalized follow-up from verified context.

FR-08

Pause before external write actions.

FR-09

Allow approve, edit or reject.

FR-10

Execute only the approved action.

FR-11

Verify the external result.

FR-12

Persist execution, approval and audit information.

FR-13

Handle failures without claiming false success.

# 16. Non-Functional Requirements

Safety: no unapproved CRM/email writes.

Explainability: every priority recommendation includes evidence/reasons.

Reliability: external action results must be verified.

Maintainability: graph nodes have clear responsibilities.

Performance: minimize unnecessary LLM calls and CRM queries.

Security: credentials and sensitive data are protected.

Traceability: major agent steps and external actions are auditable.

Provider flexibility: LLM provider can be changed through configuration.

# 17. Prioritization Logic — MVP

Use deterministic scoring before asking the LLM to interpret the result.

High-value active deal → positive score.

Proposal/negotiation stage → positive score.

Long time since last activity → positive score.

Customer explicitly requested information → strong positive score.

Existing future follow-up task → negative score.

Very recent contact → negative score.

The LLM should explain the evidence, not invent the score.

# 18. Evaluation Plan

CRM retrieval correctness

Opportunity-prioritization correctness

Grounding / hallucination rate

Tool-selection correctness

Approval enforcement rate

Successful CRM/email action rate

Verification accuracy

Failure recovery rate

End-to-end completion rate

Latency and LLM call count

# 19. Minimum Demonstration Scenario

User: "Who should I follow up with today?"

Agent retrieves real HubSpot deals and recent activities.

System selects a high-priority opportunity.

Agent explains the evidence.

Agent retrieves relevant historical communication if needed.

Communication Agent drafts a personalized message.

User reviews and approves.

Action Agent performs the approved CRM/email action.

Verification confirms the action.

Audit record is stored.

UI displays the final result.

# 20. One-Day MVP Priority

Priority

Deliverable

Reason

P0

HubSpot OAuth + MCP connection

Core real integration

P0

LangGraph state + graph

Core agent orchestration

P0

Research → real HubSpot data

Proves tool use

P0

Prioritization + strategy

Proves decision logic

P0

Follow-up generation

Core business value

P0

Human approval

Safety

P0

Approved HubSpot/Gmail action

End-to-end action

P0

Verification

Reliability

P1

Supabase persistence

Durable application state

P1

pgvector semantic memory

Advanced retrieval

P1

Minimal UI

Demo usability

P2

Deployment/polish/advanced evaluation

Only after core path works

# 21. What We Should Not Build

Uncontrolled multi-agent swarm.

Separate Redis, MongoDB and vector database without a demonstrated need.

Kubernetes or Kafka.

Fine-tuning.

Large RAG pipeline before basic CRM retrieval works.

Automatic cold-email campaigns.

Unapproved automatic sending.

Complex ML lead-scoring model for the MVP.

A fake CRM or synthetic-only demo.

# 22. Free / Low-Cost Development Strategy

The architecture should be designed to run primarily on free or open-source components during development. External free-tier quotas are not treated as guaranteed production capacity.

LangGraph, FastAPI, Streamlit, Python, Docker and pgvector are open-source technologies.

Supabase Free can provide hosted PostgreSQL and pgvector for development; verify current limits before deployment.

NVIDIA NIM/API Catalog availability and model limits should be checked at implementation time.

Groq can be retained as an inference fallback if its current free access is suitable.

Render can be used for a demo deployment, with its free-service sleep behavior documented.

# 23. Final Architecture Decision

The system will use LangGraph for orchestration, a small set of specialized agent nodes, HubSpot Remote MCP for CRM integration, Gmail MCP/API for email context/actions, NVIDIA NIM as the primary LLM provider with a configurable fallback, and Supabase PostgreSQL with pgvector for application persistence and semantic memory. HubSpot remains the CRM source of truth.

The core engineering principle is: READ → REASON → PROPOSE → APPROVE → ACT → VERIFY → AUDIT.

# 24. Implementation Order

Create repository and Python environment.

Configure HubSpot OAuth/MCP access.

Test real CRM read operation.

Create LangGraph state.

Implement Research node.

Implement deterministic prioritization.

Implement Strategy node.

Implement Communication node.

Implement human approval interrupt.

Implement approved external action.

Implement verification.

Persist run/approval/audit records.

Add semantic retrieval with pgvector if time remains.

Build minimal UI and record the end-to-end demo.

Write README documenting architecture, decisions, limitations and setup.

# 25. References

HubSpot Remote MCP: https://developers.hubspot.com/ai-tools/mcp

Gmail MCP: https://developers.google.com/workspace/gmail/api/reference/mcp

LangGraph documentation: https://docs.langchain.com/oss/python/langgraph

Supabase: https://supabase.com/

Supabase pgvector: https://supabase.com/docs/guides/database/extensions/pgvector

NVIDIA NIM documentation: https://docs.nvidia.com/nim/

Render: https://render.com/docs/free

| Component | Responsibility | Data / Access |

| --- | --- | --- |

| Orchestrator | Routes the workflow and controls state transitions. | LangGraph state |

| Research Agent | Finds relevant deals, contacts, activities and tasks. | HubSpot MCP read access |

| Prioritization | Computes explainable opportunity priority. | Structured CRM evidence |

| Strategy Agent | Determines recommended next sales action. | CRM + semantic context |

| Communication Agent | Generates a grounded personalized follow-up. | Retrieved evidence |

| Human Approval | Allows review, edit, approve or reject. | UI + LangGraph interrupt |

| Action Agent | Executes only the approved external action. | HubSpot/Gmail write capability |

| Verification Agent | Checks whether the external action succeeded. | External-system read access |

| System | Owns | Access |

| --- | --- | --- |

| HubSpot | Contacts, companies, deals, CRM activities and tasks | HubSpot MCP |

| Gmail | Email threads and mailbox data | Gmail MCP/API |

| PostgreSQL/Supabase | Application state, approvals, audit and run metadata | Direct application DB |

| pgvector | Embeddings and semantic sales-memory records | Vector similarity queries |

| Use pgvector for | Do not use pgvector for |

| --- | --- |

| Emails, meeting notes, call notes, customer requirements, proposal discussions, historical conversations | Deal amount, deal stage, contact ID, company ID, dates, tasks and other structured CRM fields |

| Layer | Technology | Purpose | Selection reason |

| --- | --- | --- | --- |

| Language | Python | Application and AI development | Strong AI, API and data ecosystem |

| LLM | NVIDIA NIM / API Catalog | Reasoning, planning and generation | Suitable primary inference option; provider abstraction retained |

| LLM fallback | Groq | Fallback inference | Fast hosted inference option |

| Orchestration | LangGraph | Stateful graph, routing, HITL and recovery | Matches multi-step workflow requirements |

| CRM | HubSpot | Real sales system of record | Direct business relevance |

| CRM integration | HubSpot Remote MCP | Agent tool access | Official MCP integration |

| Email | Gmail MCP / Gmail API | Conversation retrieval and approved sending | Real communication channel |

| Backend | FastAPI | Application API and integration layer | Fast Python implementation |

| Frontend | Streamlit | MVP interface and approval screen | Fastest implementation; replace with React later if needed |

| Database | PostgreSQL via Supabase | Application persistence | Hosted relational DB with free development tier |

| Vector search | pgvector | Semantic sales memory | Vector search inside PostgreSQL |

| Embeddings | Open embedding model | Create vectors for unstructured sales content | Avoid vendor lock-in |

| Container | Docker | Reproducible runtime | Standard deployment artifact |

| Source control | Git + GitHub | Versioning and portfolio | Standard engineering workflow |

| Deployment | Render initially | Public demo | Simple deployment; document free-tier limitations |

| Testing | pytest | Unit/integration tests | Standard Python testing |

| Observability | Structured logs; LangSmith optional | Trace agent execution | Start simple, add tracing if time permits |

| ID | Requirement |

| --- | --- |

| FR-01 | Accept natural-language sales requests. |

| FR-02 | Identify the requested sales workflow. |

| FR-03 | Retrieve relevant HubSpot CRM context. |

| FR-04 | Retrieve relevant historical communication context when needed. |

| FR-05 | Rank follow-up opportunities with explainable rules. |

| FR-06 | Explain why an opportunity is prioritized. |

| FR-07 | Generate a personalized follow-up from verified context. |

| FR-08 | Pause before external write actions. |

| FR-09 | Allow approve, edit or reject. |

| FR-10 | Execute only the approved action. |

| FR-11 | Verify the external result. |

| FR-12 | Persist execution, approval and audit information. |

| FR-13 | Handle failures without claiming false success. |

| Priority | Deliverable | Reason |

| --- | --- | --- |

| P0 | HubSpot OAuth + MCP connection | Core real integration |

| P0 | LangGraph state + graph | Core agent orchestration |

| P0 | Research → real HubSpot data | Proves tool use |

| P0 | Prioritization + strategy | Proves decision logic |

| P0 | Follow-up generation | Core business value |

| P0 | Human approval | Safety |

| P0 | Approved HubSpot/Gmail action | End-to-end action |

| P0 | Verification | Reliability |

| P1 | Supabase persistence | Durable application state |

| P1 | pgvector semantic memory | Advanced retrieval |

| P1 | Minimal UI | Demo usability |

| P2 | Deployment/polish/advanced evaluation | Only after core path works |
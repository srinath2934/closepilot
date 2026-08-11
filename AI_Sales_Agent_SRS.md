# Software Requirements Specification (SRS)

AI Sales Intelligence & Follow-Up Agent

LangGraph + Claude + MCP + HubSpot

# 1. Project Overview

The system is a hierarchical AI sales agent that connects to a real HubSpot CRM through the HubSpot Remote MCP server. It identifies sales opportunities requiring follow-up, researches CRM context, prioritizes opportunities, generates personalized follow-up messages, obtains human approval, executes approved CRM actions, and verifies the resulting CRM state.

# 2. Problem Statement

Sales representatives often need to manually inspect deals, contacts, activities and tasks to determine who requires follow-up. This can cause missed opportunities, generic communication, and inconsistent CRM updates. The proposed system automates the investigation and recommendation workflow while keeping write actions under human approval.

# 3. Goals

Connect to a real HubSpot CRM account.

Use HubSpot MCP as the tool interface between agents and CRM capabilities.

Use LangGraph for stateful workflow orchestration.

Use Claude for reasoning and personalized communication generation.

Identify and rank follow-up opportunities.

Generate context-grounded follow-up messages.

Require human approval before CRM write actions.

Execute approved CRM actions through MCP.

Verify that the requested CRM action succeeded.

Provide a demonstrable end-to-end workflow within a one-day MVP build.

# 4. Non-Goals for the One-Day MVP

Multi-agent swarm or uncontrolled autonomous agents.

Lead scraping or automated cold outreach.

RAG/vector database.

Fine-tuning.

Kafka, Kubernetes, Redis, or other unnecessary infrastructure.

Complex predictive ML lead scoring.

Unapproved automatic email sending.

Full enterprise production deployment.

# 5. Users

Primary user: Sales representative or sales manager using HubSpot.

# 6. Core User Story

As a salesperson, I want to ask "Who should I follow up with today?" so that the system can inspect my CRM, identify high-priority opportunities, explain why they need attention, draft personalized follow-ups, and execute approved CRM actions.

# 7. Functional Requirements

ID

Requirement

Description

FR-01

User Request

The system shall accept natural-language sales requests.

FR-02

Intent Detection

The system shall identify the requested sales workflow, with FIND_FOLLOWUPS as the primary MVP intent.

FR-03

CRM Retrieval

The system shall retrieve relevant HubSpot deals, contacts, activities and tasks through MCP.

FR-04

Context Assembly

The system shall assemble CRM evidence for each candidate opportunity.

FR-05

Prioritization

The system shall rank opportunities using explainable business rules such as deal value, stage, inactivity and existing follow-up tasks.

FR-06

Strategy

The system shall determine a recommended next action for a selected opportunity.

FR-07

Personalized Draft

The system shall generate a follow-up message using retrieved CRM context.

FR-08

Grounding

The system shall not invent customer facts, prices, commitments or dates not present in the available context.

FR-09

Human Approval

The system shall pause before CRM write operations and require explicit user approval.

FR-10

CRM Action

After approval, the system shall perform the permitted HubSpot write action through MCP.

FR-11

Verification

The system shall verify that the intended CRM activity/task was created or updated.

FR-12

Failure Handling

The system shall report failures and allow a bounded retry or human escalation.

FR-13

Auditability

The system shall expose the major workflow steps, selected action and result to the user.

# 8. Agent Architecture

The system shall use LangGraph as the orchestration and state-management layer. The architecture will use specialized nodes/agents rather than an uncontrolled agent swarm.

Orchestrator: manages the workflow and routing.

Research Agent: retrieves and structures HubSpot CRM evidence.

Prioritization Node: applies deterministic business scoring.

Strategy Agent: determines the recommended sales action.

Communication Agent: generates the personalized follow-up.

Human Approval Node: pauses execution until approval/rejection.

Action Agent: performs approved CRM writes through MCP.

Verification Agent: checks resulting HubSpot state and reports success/failure.

# 9. LangGraph State Requirements

user_request

intent

deals

contacts

activities

tasks

opportunities

selected_opportunity

strategy

followup_draft

approval_status

action_result

verification_result

errors

retry_count

# 10. MCP Requirements

Use HubSpot's official Remote MCP server rather than implementing a simulated CRM MCP server.

Authenticate using the supported HubSpot OAuth flow.

Discover and use the actual tools exposed by the connected MCP server.

Keep read-oriented operations separate from write-oriented actions in the application design.

Respect the permissions of the connected HubSpot user.

Do not hard-code undocumented MCP tool names.

# 11. Technology Requirements

Layer

Technology

LLM

Claude

Agent orchestration

LangGraph

CRM integration

HubSpot Remote MCP

Backend

Python + FastAPI

UI

Streamlit for MVP

Authentication

HubSpot OAuth

Version control

Git/GitHub

Containerization

Docker, optional if time remains

# 12. Non-Functional Requirements

Safety: write operations require explicit approval.

Explainability: priority recommendations must include reasons.

Reliability: failed actions must be detected and reported.

Maintainability: graph nodes should have clear single responsibilities.

Security: secrets and OAuth credentials must be stored in environment variables or secure secret storage.

Traceability: important tool calls and action outcomes should be visible/logged.

Performance: the MVP should avoid unnecessary LLM calls and repeated CRM queries.

# 13. Priority Scoring — MVP

Recommended deterministic scoring inputs:

High deal value: positive score.

Proposal/negotiation stage: positive score.

Long period since last activity: positive score.

Explicit customer request awaiting response: strong positive score.

Existing scheduled follow-up task: negative score.

Recently contacted: negative score.

# 14. Safety Rules

The agent may read CRM information according to the connected user's permissions.

The agent must not send or log a follow-up without approval in the MVP.

The communication agent must use only verified CRM context.

The action agent must execute only the approved action.

Retries must be bounded; no infinite autonomous retry loop.

# 15. End-to-End Acceptance Test

User asks: 'Who should I follow up with today?'

LangGraph starts the workflow.

Research retrieves real HubSpot opportunities.

Prioritization ranks the opportunities.

Strategy explains why the highest-priority opportunity needs attention.

Communication agent drafts a context-grounded follow-up.

UI pauses for human approval.

User approves the action.

Action agent performs the approved HubSpot action through MCP.

Verification confirms the resulting CRM state.

System reports success and the recorded action.

# 16. One-Day Implementation Priority

Priority

Deliverable

P0

HubSpot OAuth + Remote MCP connection

P0

LangGraph state and basic graph

P0

Research → real HubSpot deal retrieval

P0

Prioritization → strategy

P0

Follow-up generation

P0

Human approval

P0

Approved HubSpot write

P1

Verification and bounded retry

P1

Minimal Streamlit UI

P2

Docker, polished UI, extended tests

# 17. Success Criteria

A real HubSpot account can be connected.

The agent can retrieve at least one real deal/contact context through MCP.

LangGraph can move through research, strategy and communication steps.

A personalized follow-up can be generated from CRM evidence.

The workflow pauses for human approval.

An approved action can be written back to HubSpot.

The system can verify/report the result.

The entire workflow can be demonstrated live.

# 18. Future Extensions

Automatic daily sales briefings.

Deal-risk detection.

Lead qualification.

Email reply analysis.

Calendar-aware follow-up scheduling.

CRM data-quality agent.

Sales forecasting.

Multi-channel outreach with additional approval policies.

Evaluation datasets and agent performance metrics.

| ID | Requirement | Description |

| --- | --- | --- |

| FR-01 | User Request | The system shall accept natural-language sales requests. |

| FR-02 | Intent Detection | The system shall identify the requested sales workflow, with FIND_FOLLOWUPS as the primary MVP intent. |

| FR-03 | CRM Retrieval | The system shall retrieve relevant HubSpot deals, contacts, activities and tasks through MCP. |

| FR-04 | Context Assembly | The system shall assemble CRM evidence for each candidate opportunity. |

| FR-05 | Prioritization | The system shall rank opportunities using explainable business rules such as deal value, stage, inactivity and existing follow-up tasks. |

| FR-06 | Strategy | The system shall determine a recommended next action for a selected opportunity. |

| FR-07 | Personalized Draft | The system shall generate a follow-up message using retrieved CRM context. |

| FR-08 | Grounding | The system shall not invent customer facts, prices, commitments or dates not present in the available context. |

| FR-09 | Human Approval | The system shall pause before CRM write operations and require explicit user approval. |

| FR-10 | CRM Action | After approval, the system shall perform the permitted HubSpot write action through MCP. |

| FR-11 | Verification | The system shall verify that the intended CRM activity/task was created or updated. |

| FR-12 | Failure Handling | The system shall report failures and allow a bounded retry or human escalation. |

| FR-13 | Auditability | The system shall expose the major workflow steps, selected action and result to the user. |

| Layer | Technology |

| --- | --- |

| LLM | Claude |

| Agent orchestration | LangGraph |

| CRM integration | HubSpot Remote MCP |

| Backend | Python + FastAPI |

| UI | Streamlit for MVP |

| Authentication | HubSpot OAuth |

| Version control | Git/GitHub |

| Containerization | Docker, optional if time remains |

| Priority | Deliverable |

| --- | --- |

| P0 | HubSpot OAuth + Remote MCP connection |

| P0 | LangGraph state and basic graph |

| P0 | Research → real HubSpot deal retrieval |

| P0 | Prioritization → strategy |

| P0 | Follow-up generation |

| P0 | Human approval |

| P0 | Approved HubSpot write |

| P1 | Verification and bounded retry |

| P1 | Minimal Streamlit UI |

| P2 | Docker, polished UI, extended tests |
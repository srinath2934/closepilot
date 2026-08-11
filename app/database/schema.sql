-- =========================================================
-- GWC AI Sales Agent - Supabase PostgreSQL Database Schema
-- Run this in your Supabase SQL Editor (supabase.com -> SQL Editor)
-- =========================================================

-- Enable pgvector extension for semantic sales memory
CREATE EXTENSION IF NOT EXISTS vector;

-- 1. Agent Threads Table
CREATE TABLE IF NOT EXISTS agent_threads (
    thread_id TEXT PRIMARY KEY,
    user_id TEXT DEFAULT 'default_user',
    status TEXT NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Agent Execution Runs Table
CREATE TABLE IF NOT EXISTS agent_runs (
    run_id TEXT PRIMARY KEY,
    thread_id TEXT REFERENCES agent_threads(thread_id) ON DELETE CASCADE,
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'RUNNING',
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    error TEXT
);

-- 3. Human Approval Requests Table
CREATE TABLE IF NOT EXISTS approval_requests (
    approval_id TEXT PRIMARY KEY,
    thread_id TEXT REFERENCES agent_threads(thread_id) ON DELETE CASCADE,
    run_id TEXT,
    action_type TEXT NOT NULL,
    target_id TEXT,
    proposed_content JSONB NOT NULL,
    status TEXT NOT NULL DEFAULT 'PENDING',
    reviewed_at TIMESTAMP WITH TIME ZONE,
    user_modifications JSONB
);

-- 4. Audit Events Trail Table
CREATE TABLE IF NOT EXISTS audit_events (
    event_id TEXT PRIMARY KEY,
    thread_id TEXT REFERENCES agent_threads(thread_id) ON DELETE CASCADE,
    node TEXT NOT NULL,
    tool TEXT,
    action TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'SUCCESS',
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB
);

-- 5. Semantic Sales Memory & Conversation Embeddings Table
CREATE TABLE IF NOT EXISTS conversation_embeddings (
    id BIGSERIAL PRIMARY KEY,
    source_type TEXT NOT NULL, -- 'email', 'meeting_notes', 'call_transcript'
    source_id TEXT,
    deal_id TEXT,
    content TEXT NOT NULL,
    embedding VECTOR(1536), -- Standard embedding dimension
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for fast query performance
CREATE INDEX IF NOT EXISTS idx_agent_runs_thread ON agent_runs(thread_id);
CREATE INDEX IF NOT EXISTS idx_audit_events_thread ON audit_events(thread_id);
CREATE INDEX IF NOT EXISTS idx_approval_requests_thread ON approval_requests(thread_id);

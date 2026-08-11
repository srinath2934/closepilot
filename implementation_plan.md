# GWC AI Sales Agent — Complete Bug Audit & Fix Plan

## Problem Statement
The user reports that the MVP has significant bugs: the CLI demo output is garbled (text overwriting itself), the Streamlit "Analyze CRM" button is non-functional, the UI is incomplete, and backend features are missing.

## Bug Analysis (Comprehensive Audit)

### BUG 1: CLI `run_demo.py` garbled output (text overwriting itself)
**Root Cause:** The `bullet` character `•` (`\u2022`) used in print statements is rendered as a `\r` (carriage return) by the Windows `cp1252` terminal, causing lines to overwrite each other.
**Fix:** Replace `•` with ASCII-safe `-` in `run_demo.py`.

---

### BUG 2: Streamlit `asyncio.run()` crashes inside Streamlit's own event loop
**Root Cause:** Streamlit already runs its own `asyncio` event loop. Calling `asyncio.run()` from within a Streamlit callback raises `RuntimeError: This event loop is already running` or silently fails. The previous code used `asyncio.new_event_loop()` which had its own problems, but `asyncio.run()` is also wrong.
**Fix:** Use `nest_asyncio.apply()` to patch the running loop, then use `asyncio.get_event_loop().run_until_complete()`. Or better: create a dedicated thread with its own loop.

---

### BUG 3: No error handling / user feedback when workflow fails
**Root Cause:** If `sales_graph.ainvoke()` raises an exception, the Streamlit UI shows nothing — it just silently fails. No `try/except` around the workflow invocation in `frontend/app.py`.
**Fix:** Wrap in `try/except`, display `st.error()`.

---

### BUG 4: The data is NOT from CRM — it's all hardcoded sandbox data
**Root Cause:** Even though `HUBSPOT_USE_MOCK=false`, the HubSpot API calls may fail silently and fall back to `SANDBOX_DEALS` (line 188 of `hubspot.py`). The user sees the same 4 hardcoded deals every time. The HubSpot OAuth token may also be expired. There's no feedback to the user about which data source is being used.
**Fix:** Add clear CRM source indicators in the UI. Log and display when falling back to sandbox.

---

### BUG 5: `frontend/app.py` imports `sales_graph` at module level — stale graph instance
**Root Cause:** `from app.graph.graph import sales_graph` creates the graph once at import time. The global `sales_graph` in `graph.py` (line 72) uses a single `MemorySaver()`. But Streamlit re-runs the entire script on every interaction, and the module-level import creates a cached singleton. This means the same `MemorySaver` is reused across sessions, but state can bleed between sessions or get corrupted.
**Fix:** The current approach works for MVP, but we should ensure thread isolation (each session gets unique `thread_id`, which it does).

---

### BUG 6: Missing backend API features
**Root Cause:** The FastAPI backend (`app/main.py`) has endpoints but they're not connected to the Streamlit frontend. The Streamlit app calls `sales_graph` directly (bypassing the API). Missing API endpoints:
- No `/api/deals/seed` endpoint to seed CRM data
- No `/api/settings` endpoint to view/change config
- No health check for HubSpot connection status
**Fix:** Add missing backend endpoints and connect frontend to use them where appropriate.

---

### BUG 7: Streamlit UI is incomplete — missing features
**Root Cause:** The UI only has:
- A text input + Analyze button
- Ranked opportunities display
- Strategy card
- Draft editor + approve/reject
- Completion card

Missing from UI:
- CRM connection status indicator (is it live or sandbox?)
- Individual deal details view
- Activity history / timeline
- Error display panel
- Session history
- Settings panel in sidebar
**Fix:** Add connection status, error panel, and deal detail views.

---

### BUG 8: `run_demo.py` uses `•` bullet which fails on Windows cp1252 terminal
**Root Cause:** Same as BUG 1 — the `•` character (U+2022) is not in Windows code page 1252.
**Fix:** Replace with ASCII `-`.

---

## Proposed Changes

### Phase 1: Fix Critical Bugs (Backend & CLI)

#### [MODIFY] [run_demo.py](file:///d:/sales%20agent/run_demo.py)
- Replace `•` bullet characters with ASCII `-` to fix garbled terminal output on Windows

#### [MODIFY] [frontend/app.py](file:///d:/sales%20agent/frontend/app.py)
- Fix async execution: use `nest_asyncio` to allow `asyncio.run()` inside Streamlit's loop, or use a background thread
- Add `try/except` with `st.error()` around workflow invocation
- Add CRM connection status indicator (Live vs Sandbox)
- Add error display panel
- Add deal detail expansion
- Fix approve/reject button async handling

#### [MODIFY] [requirements.txt](file:///d:/sales%20agent/requirements.txt)
- Add `nest_asyncio` dependency

---

### Phase 2: Backend Completeness

#### [MODIFY] [app/main.py](file:///d:/sales%20agent/app/main.py)
- Add `GET /api/health` endpoint with HubSpot connection test
- Add `GET /api/settings` endpoint to expose current configuration
- Add `POST /api/deals/seed` endpoint to seed test data into HubSpot

---

### Phase 3: UI Polish & Missing Features

#### [MODIFY] [frontend/app.py](file:///d:/sales%20agent/frontend/app.py)
- Add sidebar CRM health status (live ping test)
- Add expandable deal detail cards with notes, contact info, activity timeline
- Add error log panel at bottom
- Add session management improvements

---

## Verification Plan

### Automated Tests
```bash
uv run pytest tests/ -v
```

### Manual Verification
1. Run `uv run python run_demo.py` — verify clean, non-garbled output
2. Open `http://localhost:8501` — verify "Analyze CRM" button works
3. Verify CRM status indicator shows correct mode
4. Verify approve/reject buttons function
5. Verify error handling shows user-friendly messages

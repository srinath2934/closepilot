#!/bin/bash
set -e

echo "=================================================="
echo "[*] Launching ClosePilot AI Sales Copilot Services"
echo "=================================================="

# 1. Start FastAPI Backend on port 8000 in background
echo "[*] Starting FastAPI Backend on 0.0.0.0:8000..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Wait 2 seconds for backend to initialize
sleep 2

# 2. Start Streamlit Frontend on port 8501 in foreground
echo "[*] Starting Streamlit Dashboard on 0.0.0.0:8501..."
streamlit run frontend/app.py --server.port 8501 --server.address 0.0.0.0

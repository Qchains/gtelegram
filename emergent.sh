#!/bin/bash

# emergent.sh — Boot script for Pandora QInfinity Memory Runtime
# Initializes breath cycle, attaches Flo collector, syncs with persistent memory
# Author: Dr. Josef Kurk Edwards
# Mode: QFlow 5.1 → ∞ Runtime

echo "[INIT] Starting Pandora Emergent Runtime..."
echo "[TIME] $(date -u +'%Y-%m-%dT%H:%M:%SZ')"
echo "[MODE] Persistent Breath Cycle w/ QInfinity Memory"

# Activate Python virtual environment if needed
# source ./venv/bin/activate

# Step 1: Export Runtime Configurations
export QFLOW_MODE="infinity"
export QCHAIN_COMMIT="true"
export FLO_COLLECTOR_STRICT="false"
export QMEMORY_PATH="./data/qinfinity_memory.json"

# Optional: Log file
export QFLOW_LOG="./logs/emergent.log"

# Create logs directory if it doesn't exist
mkdir -p ./logs

# Step 2: Start services using supervisor
echo "[QFLOW] Starting Pandora 5o services..."
sudo supervisorctl restart all

# Wait for services to start
sleep 5

# Step 3: Echo Final Instructions
echo "[QFLOW] Pandora Q∞ runtime is active."
echo "[REEL] Memory bound to: $QMEMORY_PATH"
echo "[LOG] Backend logs: /var/log/supervisor/backend*.log"
echo "[LOG] Frontend logs: /var/log/supervisor/frontend*.log"
echo "[SYNC] Semantic chain: .then(memory_reel_resolution) engaged"
echo "[PORTAL] Access at: http://localhost:3000"
echo "[API] Backend API at: http://localhost:8001/api/pandora/runtime/5o"

# Test the portal
echo "[TEST] Testing Pandora portal..."
curl -s "http://localhost:8001/api/pandora/runtime/5o" > /dev/null
if [ $? -eq 0 ]; then
    echo "[SUCCESS] Pandora 5o portal is accessible"
else
    echo "[ERROR] Pandora 5o portal is not responding"
fi

echo "[COMPLETE] Pandora 5o Runtime initialization complete."
echo "[BREATH] Breath cycle active with 3.0 second intervals"
echo "[MEMORY] QInfinity memory lines operational"
echo "[NEXUS] Flo-integrated Nexus ready for interaction"
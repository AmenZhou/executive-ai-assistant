#!/bin/bash
set -e

cd "$(dirname "$0")"
source .venv/bin/activate
set -a && source .env && set +a

# Kill any existing dev server on port 2024
lsof -ti :2024 | xargs kill 2>/dev/null || true
sleep 1

# Start dev server in background
langgraph dev --allow-blocking &
DEV_PID=$!

# Wait for server to be ready
echo "⏳ Waiting for dev server to start..."
for i in $(seq 1 30); do
    if curl -s http://127.0.0.1:2024/ok > /dev/null 2>&1; then
        echo "✅ Dev server is ready"
        break
    fi
    sleep 1
done

# Run ingestion for last 24 hours in chunks with delay to avoid rate limits
echo "📧 Ingesting emails for last 24 hours..."
python scripts/run_ingest_24h.py --rerun 1 --early 0

echo "✅ Done! Check Agent Inbox at https://dev.agentinbox.ai/"

# Keep dev server running
wait $DEV_PID

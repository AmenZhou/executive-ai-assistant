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

# Run ingestion for last 24 hours in 4 batches to avoid rate limits
echo "📧 Ingesting emails: 24h ago to 18h ago..."
python scripts/run_ingest.py --minutes-since 1440 --minutes-until 1080 --rerun 1 --early 0

echo "📧 Ingesting emails: 18h ago to 12h ago..."
python scripts/run_ingest.py --minutes-since 1080 --minutes-until 720 --rerun 1 --early 0

echo "📧 Ingesting emails: 12h ago to 6h ago..."
python scripts/run_ingest.py --minutes-since 720 --minutes-until 360 --rerun 1 --early 0

echo "📧 Ingesting emails: 6h ago to now..."
python scripts/run_ingest.py --minutes-since 360 --minutes-until 0 --rerun 1 --early 0

echo "✅ Done! Check Agent Inbox at https://dev.agentinbox.ai/"

# Keep dev server running
wait $DEV_PID

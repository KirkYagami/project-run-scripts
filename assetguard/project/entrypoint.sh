#!/bin/sh
# Start the AssetGuard AI REST service (8081) and dashboard (8080) in one container.
set -e

if [ -z "$GEMINI_API_KEY" ]; then
    echo "GEMINI_API_KEY is not set. Pass it with --env-file .env or -e GEMINI_API_KEY=..." >&2
    exit 1
fi

# Creates tables and seed accounts; leaves existing data alone, so safe on every start.
python run_database_setup.py

python run_api_service.py &
API_PID=$!

python -m streamlit run run_dashboard.py &
DASH_PID=$!

trap 'kill -TERM $API_PID $DASH_PID 2>/dev/null' INT TERM

# If either process exits, stop the other so the container exits and can be restarted.
while kill -0 $API_PID 2>/dev/null && kill -0 $DASH_PID 2>/dev/null; do
    sleep 2
done
echo "A service stopped; shutting the container down." >&2
kill -TERM $API_PID $DASH_PID 2>/dev/null || true
wait
exit 1

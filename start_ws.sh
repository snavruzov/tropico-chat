#!/bin/sh
# Start Uvicorn processes
echo "Starting Uvicorn."

# Running Uvicorn server
exec uvicorn api.server:app --workers 2 --host 0.0.0.0 --port 8000 --ws websockets --ws-ping-interval 2.0 --proxy-headers

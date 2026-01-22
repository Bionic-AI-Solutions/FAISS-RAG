#!/bin/bash
# Script to properly restart frontend on port 3001

set -e

echo "Stopping all Node processes..."
killall -9 node npm next 2>/dev/null || true
sleep 2

echo "Cleaning Next.js lock files..."
cd /workspaces/mem0-rag/frontend
rm -rf .next/dev/lock .next/cache 2>/dev/null || true

echo "Waiting for port 3001 to be free..."
for i in {1..10}; do
    if ! timeout 1 bash -c "echo > /dev/tcp/localhost/3001" 2>/dev/null; then
        echo "Port 3001 is free"
        break
    fi
    echo "Port still in use, waiting... ($i/10)"
    sleep 1
done

echo "Starting frontend on port 3001..."
cd /workspaces/mem0-rag/frontend
npm run dev -- -p 3001 > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > /tmp/frontend.pid

echo "Waiting for frontend to start..."
sleep 15

if kill -0 $FRONTEND_PID 2>/dev/null; then
    echo "✅ Frontend started successfully (PID: $FRONTEND_PID)"
    echo "Logs:"
    tail -20 /tmp/frontend.log
else
    echo "❌ Frontend failed to start. Check logs:"
    tail -50 /tmp/frontend.log
    exit 1
fi

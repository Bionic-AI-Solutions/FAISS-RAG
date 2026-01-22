#!/bin/bash
# Force kill anything on port 3001

echo "Attempting to free port 3001..."

# Kill all node processes
killall -9 node npm next 2>/dev/null || true

# Try to find and kill process on port 3001 using different methods
for cmd in "lsof -ti:3001" "fuser 3001/tcp" "ss -tlnp | grep 3001"; do
    PIDS=$(eval $cmd 2>/dev/null | grep -oE '[0-9]+' | head -5)
    if [ ! -z "$PIDS" ]; then
        echo "Found PIDs: $PIDS"
        for pid in $PIDS; do
            kill -9 $pid 2>/dev/null && echo "Killed PID $pid" || true
        done
    fi
done

# Wait for port to be released
echo "Waiting for port to be released..."
for i in {1..15}; do
    if ! python3 -c "import socket; s=socket.socket(); r=s.connect_ex(('localhost', 3001)); s.close(); exit(0 if r==0 else 1)" 2>/dev/null; then
        echo "✅ Port 3001 is now free!"
        exit 0
    fi
    sleep 1
done

echo "⚠️  Port 3001 may still be in use (could be TIME_WAIT state)"
echo "You may need to wait a bit longer or restart the system"

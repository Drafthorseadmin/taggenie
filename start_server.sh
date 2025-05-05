#!/bin/bash

# Function to check if a port is in use
check_port() {
    lsof -i :$1 >/dev/null 2>&1
    return $?
}

# Kill any existing uvicorn processes
echo "Killing any existing uvicorn processes..."
pkill -9 -f uvicorn

# Wait a moment to ensure the port is freed
sleep 2

# Check if port 8001 is still in use
if check_port 8001; then
    echo "Port 8001 is still in use. Trying to find and kill the process..."
    PORT_PID=$(lsof -ti:8001)
    if [ ! -z "$PORT_PID" ]; then
        kill -9 $PORT_PID
        sleep 1
    fi
fi

# Start the backend server
echo "Starting backend server..."
cd app
nohup uvicorn main:app --host 0.0.0.0 --port 8001 --workers 4 > ../backend.log 2>&1 &
BACKEND_PID=$!

# Wait a moment for the backend to start
sleep 2

# Start the frontend server
echo "Starting frontend server..."
cd ../frontend

# Check if we're in production mode
if [ "$NODE_ENV" = "production" ]; then
    # In production, serve the built files
    nohup serve -s build -l 3000 > ../frontend.log 2>&1 &
else
    # In development, use the development server
    nohup npm start > ../frontend.log 2>&1 &
fi

FRONTEND_PID=$!

echo "Servers started in the background. Check backend.log and frontend.log for output."
echo "To stop the servers, run: pkill -f 'uvicorn|node'" 
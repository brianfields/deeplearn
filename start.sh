#!/bin/bash

# DeepLearn Start Script
# This script starts the backend, mobile app, admin dashboard, and web app

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Starting DeepLearn Platform...${NC}"

# Function to kill processes on specific ports
kill_port() {
    local port=$1
    local pid=$(lsof -ti:$port 2>/dev/null)
    if [ ! -z "$pid" ]; then
        echo -e "${BLUE}Killing process on port $port (PID: $pid)${NC}"
        kill -9 $pid 2>/dev/null || true
    fi
}

# Kill existing processes on required ports
echo -e "${BLUE}Checking for existing processes on required ports...${NC}"
kill_port 8000  # Backend
kill_port 3000  # Admin dashboard
kill_port 8081  # Mobile app
kill_port 8082  # Web app

# Function to cleanup background processes on exit
cleanup() {
    echo -e "${BLUE}Shutting down services...${NC}"
    kill $BACKEND_PID $MOBILE_PID $ADMIN_PID $WEB_PID 2>/dev/null || true
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Start backend server
echo -e "${GREEN}Starting backend server...${NC}"
cd backend
source venv/bin/activate
python server.py &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3


# Start admin dashboard
echo -e "${GREEN}Starting admin dashboard...${NC}"
cd ../admin
npm run dev &
ADMIN_PID=$!

echo -e "${GREEN}DeepLearn Platform is starting up!${NC}"
echo -e "${BLUE}Backend API: http://localhost:8000${NC}"
echo -e "${BLUE}API Docs: http://localhost:8000/docs${NC}"
echo -e "${BLUE}Mobile app: Expo development server starting...${NC}"
echo -e "${BLUE}Admin dashboard: http://localhost:3000${NC}"
echo -e "${BLUE}Web app: http://localhost:8082${NC}"
echo -e "${BLUE}Press Ctrl+C to stop all services${NC}"

# Start mobile app
# echo -e "${GREEN}Starting mobile app...${NC}"
cd ../mobile
# npm run ios &
# MOBILE_PID=$!

# Start web app
echo -e "${GREEN}Starting web app...${NC}"
npm run web
WEB_PID=$!

# Wait for background processes
wait

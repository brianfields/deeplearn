#!/bin/bash

# DeepLearn Start Script
# This script starts both the backend and mobile apps

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Starting DeepLearn Platform...${NC}"

# Function to cleanup background processes on exit
cleanup() {
    echo -e "${BLUE}Shutting down services...${NC}"
    kill $BACKEND_PID $MOBILE_PID 2>/dev/null || true
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Start backend server
echo -e "${GREEN}Starting backend server...${NC}"
cd backend
source ../deeplearn/bin/activate
python start_server.py &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Start mobile app
echo -e "${GREEN}Starting mobile app...${NC}"
cd ../mobile
npm start &
MOBILE_PID=$!

echo -e "${GREEN}DeepLearn Platform is starting up!${NC}"
echo -e "${BLUE}Backend API: http://localhost:8000${NC}"
echo -e "${BLUE}API Docs: http://localhost:8000/docs${NC}"
echo -e "${BLUE}Mobile app: Expo development server starting...${NC}"
echo -e "${BLUE}Press Ctrl+C to stop all services${NC}"

# Wait for background processes
wait

#!/bin/bash

# DeepLearn Start Script
# This script starts the backend, mobile app, admin dashboard, and web app

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Starting DeepLearn Platform...${NC}"

# Defaults (can be overridden by CLI flags)
ADMIN_ENABLED=1
START_WEB=1
START_IOS=0
PLATFORMS_SPECIFIED=0

# Usage helper
usage() {
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --admin | --no-admin     Enable/disable admin server (default: enabled)"
    echo "  --web                    Start Expo web (default if no platform flags)"
    echo "  --ios                    Start Expo iOS"
    echo "  --only-web               Start web only (disables iOS)"
    echo "  --only-ios               Start iOS only (disables web)"
    echo "  -h, --help               Show this help"
}

# Parse args
while [[ $# -gt 0 ]]; do
    case "$1" in
        --admin)
            ADMIN_ENABLED=1
            ;;
        --no-admin)
            ADMIN_ENABLED=0
            ;;
        --only-web)
            PLATFORMS_SPECIFIED=1
            START_WEB=1
            START_IOS=0
            ;;
        --only-ios)
            PLATFORMS_SPECIFIED=1
            START_WEB=0
            START_IOS=1
            ;;
        --web)
            if [ $PLATFORMS_SPECIFIED -eq 0 ]; then
                # First platform flag replaces defaults
                START_WEB=0
                START_IOS=0
            fi
            PLATFORMS_SPECIFIED=1
            START_WEB=1
            ;;
        --ios)
            if [ $PLATFORMS_SPECIFIED -eq 0 ]; then
                # First platform flag replaces defaults
                START_WEB=0
                START_IOS=0
            fi
            PLATFORMS_SPECIFIED=1
            START_IOS=1
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
    shift
done

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


if [ $ADMIN_ENABLED -eq 1 ]; then
echo -e "${GREEN}Starting admin dashboard...${NC}"
cd ../admin
npm run dev &
ADMIN_PID=$!
else
echo -e "${BLUE}Admin dashboard disabled by flag${NC}"
cd ../admin
fi

echo -e "${GREEN}DeepLearn Platform is starting up!${NC}"
echo -e "${BLUE}Backend API: http://localhost:8000${NC}"
echo -e "${BLUE}API Docs: http://localhost:8000/docs${NC}"
if [ $ADMIN_ENABLED -eq 1 ]; then
echo -e "${BLUE}Admin dashboard: http://localhost:3000${NC}"
else
echo -e "${BLUE}Admin dashboard: disabled${NC}"
fi
if [ $START_IOS -eq 1 ]; then
echo -e "${BLUE}iOS app: Expo development server starting...${NC}"
fi
if [ $START_WEB -eq 1 ]; then
echo -e "${BLUE}Web app: http://localhost:8082${NC}"
fi
echo -e "${BLUE}Press Ctrl+C to stop all services${NC}"

# Start mobile app
# echo -e "${GREEN}Starting mobile app...${NC}"
cd ../mobile
if [ $START_IOS -eq 1 ]; then
echo -e "${GREEN}Starting iOS app...${NC}"
npm run ios &
MOBILE_PID=$!
fi

# Start web app
if [ $START_WEB -eq 1 ]; then
echo -e "${GREEN}Starting web app...${NC}"
npm run web &
WEB_PID=$!
fi

# Wait for background processes
wait

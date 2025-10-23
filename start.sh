#!/bin/bash

# DeepLearn Start Script
# This script starts the backend, Redis server, ARQ worker, mobile app, admin dashboard, and web app
#
# Services started:
# - Redis server (localhost:6379) - Required for ARQ task queue
# - Backend API server (localhost:8000) - Main application server
# - ARQ worker - Background task processor for flows
# - Admin dashboard (localhost:3000) - Management interface
# - Mobile/Web apps - Frontend applications

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
REDIS_ENABLED=1
WORKER_ENABLED=1

# Usage helper
usage() {
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --admin | --no-admin     Enable/disable admin server (default: enabled)"
    echo "  --redis | --no-redis     Enable/disable Redis server (default: enabled)"
    echo "  --worker | --no-worker   Enable/disable ARQ worker (default: enabled)"
    echo "  --web | --no-web         Enable/disable Expo web (default: enabled)"
    echo "  --ios | --no-ios         Enable/disable Expo iOS (default: disabled)"
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
        --redis)
            REDIS_ENABLED=1
            ;;
        --no-redis)
            REDIS_ENABLED=0
            ;;
        --worker)
            WORKER_ENABLED=1
            ;;
        --no-worker)
            WORKER_ENABLED=0
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
        --no-web)
            START_WEB=0
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
        --no-ios)
            START_IOS=0
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
# kill_port 8081  # Mobile app
# kill_port 8082  # Web app
kill_port 6379  # Redis

# Function to cleanup background processes on exit
cleanup() {
    echo -e "${BLUE}Shutting down services...${NC}"
    kill $BACKEND_PID $MOBILE_PID $ADMIN_PID $WEB_PID $REDIS_PID $WORKER_PID 2>/dev/null || true
    # Clean up worker log file
    rm -f worker.log 2>/dev/null || true
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Start Redis server (required for ARQ task queue)
if [ $REDIS_ENABLED -eq 1 ]; then
    echo -e "${GREEN}Starting Redis server...${NC}"

    # Check if Redis is already running
    if pgrep -f "redis-server.*6379" >/dev/null 2>&1; then
        REDIS_PID=$(pgrep -f "redis-server.*6379" | head -1)
        echo -e "${GREEN}Redis server already running (PID: $REDIS_PID)${NC}"
    elif command -v redis-server >/dev/null 2>&1; then
        # Start Redis server
        redis-server --daemonize yes --port 6379 --bind 127.0.0.1 --save "" --appendonly no
        sleep 2  # Give Redis time to start

        # Verify Redis started successfully
        if redis-cli ping >/dev/null 2>&1; then
            REDIS_PID=$(pgrep -f "redis-server.*6379" | head -1)
            echo -e "${GREEN}Redis server started successfully (PID: $REDIS_PID)${NC}"
        else
            echo -e "${BLUE}Warning: Redis server failed to start properly${NC}"
            REDIS_PID=""
        fi
    else
        echo -e "${BLUE}Warning: Redis not installed. Install with: brew install redis (macOS) or apt-get install redis-server (Ubuntu)${NC}"
        echo -e "${BLUE}ARQ worker will not function without Redis${NC}"
        REDIS_PID=""
    fi
else
    echo -e "${BLUE}Redis server disabled by flag${NC}"
    REDIS_PID=""
fi

# Start backend server
echo -e "${GREEN}Starting backend server...${NC}"
cd backend
source venv/bin/activate
python server.py &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Start ARQ worker (for background task processing)
if [ $WORKER_ENABLED -eq 1 ]; then
    echo -e "${GREEN}Starting ARQ worker...${NC}"

    # Check if Redis is available (either started by us or already running)
    if redis-cli ping >/dev/null 2>&1; then
        # Check if ARQ dependencies are available
        if python -c "import arq, redis" 2>/dev/null; then
            # Ensure handler registrations are loaded by the worker
            export TASK_QUEUE_REGISTRATIONS=modules.content_creator.public
            # Use ARQ's native command line interface for proper event loop handling
            nohup bash -c "cd $(pwd) && source venv/bin/activate && python -m arq modules.task_queue.tasks.WorkerSettings" > worker.log 2>&1 &
            WORKER_PID=$!
            sleep 2  # Give worker more time to start

            # Check if worker process is still running (didn't crash immediately)
            if kill -0 $WORKER_PID 2>/dev/null; then
                echo -e "${GREEN}ARQ worker started successfully (PID: $WORKER_PID)${NC}"
                echo -e "${BLUE}Worker logs: worker.log${NC}"
            else
                echo -e "${BLUE}Warning: ARQ worker failed to start (check worker.log)${NC}"
                if [ -f worker.log ]; then
                    echo -e "${BLUE}Last few lines of worker.log:${NC}"
                    tail -5 worker.log
                fi
                WORKER_PID=""
            fi
        else
            echo -e "${BLUE}Warning: ARQ worker dependencies not found. Install with: pip install arq redis${NC}"
            WORKER_PID=""
        fi
    else
        echo -e "${BLUE}Warning: ARQ worker requires Redis to be running. Redis connection failed.${NC}"
        WORKER_PID=""
    fi
else
    echo -e "${BLUE}ARQ worker disabled by flag${NC}"
    WORKER_PID=""
fi

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
if [ $REDIS_ENABLED -eq 1 ]; then
echo -e "${BLUE}Redis server: localhost:6379${NC}"
else
echo -e "${BLUE}Redis server: disabled${NC}"
fi
if [ $WORKER_ENABLED -eq 1 ]; then
echo -e "${BLUE}ARQ worker: background task processing enabled${NC}"
else
echo -e "${BLUE}ARQ worker: disabled${NC}"
fi
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

# Start mobile app (Expo dev server only; Maestro opens the URL)
# echo -e "${GREEN}Starting mobile app...${NC}"
cd ../mobile
if [ $START_IOS -eq 1 ]; then
echo -e "${GREEN}Starting Expo dev server (iOS)...${NC}"
npm run ios &
MOBILE_PID=$!
fi

# # Start web app
# if [ $START_WEB -eq 1 ]; then
# echo -e "${GREEN}Starting web app...${NC}"
# npm run web &
# WEB_PID=$!
# fi

# Wait for background processes
wait

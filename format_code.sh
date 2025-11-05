#!/bin/bash

# Code Formatting and Linting Script
# This script runs formatting and linting tools across all codebases
#
# Usage: ./format_code.sh [--no-venv]
#   --no-venv: Skip virtual environment activation (use current Python environment)

# Track overall success
OVERALL_SUCCESS=true

# Parse command-line arguments
USE_VENV=true
while [[ $# -gt 0 ]]; do
    case $1 in
        --no-venv)
            USE_VENV=false
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--no-venv]"
            exit 1
            ;;
    esac
done

# Function to run a command and report result
run_command() {
    local command_name="$1"
    local command="$2"
    local work_dir="$3"

    echo "Running $command_name..."
    if [ -n "$work_dir" ]; then
        cd "$work_dir"
    fi

    if eval "$command"; then
        echo "[SUCCESS] $command_name completed"
        if [ -n "$work_dir" ]; then
            cd ..
        fi
        return 0
    else
        echo "[FAILED] $command_name failed"
        if [ -n "$work_dir" ]; then
            cd ..
        fi
        OVERALL_SUCCESS=false
        return 1
    fi
}

echo "Starting code formatting and linting..."

# Construct backend commands based on venv usage
if [ "$USE_VENV" = true ]; then
    BACKEND_PREFIX="([ -f venv/bin/activate ] && source venv/bin/activate || source ../venv/bin/activate) && "
    echo "Using virtual environment for backend commands"
else
    BACKEND_PREFIX=""
    echo "Using current Python environment (--no-venv)"
fi

# Backend: Ruff format and lint
if run_command "backend ruff format" "ruff format" "backend"; then
    echo "[PASS] Backend formatting completed"
else
    echo "[FAIL] Backend formatting failed"
fi

if run_command "backend ruff lint fix" "ruff check --fix" "backend"; then
    echo "[PASS] Backend linting completed"
else
    echo "[FAIL] Backend linting failed"
fi

# Admin: Next.js lint (includes formatting via Prettier integration)
# Note: Admin may fail due to Node.js version requirements, but we'll try anyway
if run_command "admin lint" "npm run lint" "admin"; then
    echo "[PASS] Admin linting completed"
else
    echo "[WARN] Admin linting failed (possibly due to Node.js version)"
fi

if run_command "admin tsc" "npx tsc --noEmit" "admin"; then
    echo "[PASS] Admin type checking completed"
else
    echo "[FAIL] Admin type checking failed"
fi

# Mobile: Prettier format and ESLint fix
if run_command "mobile format" "npm run format" "mobile"; then
    echo "[PASS] Mobile formatting completed"
else
    echo "[FAIL] Mobile formatting failed"
fi

if run_command "mobile lint fix" "npm run lint:fix" "mobile"; then
    echo "[PASS] Mobile linting completed"
else
    echo "[FAIL] Mobile linting failed"
fi

if run_command "mobile tsc" "npx tsc --noEmit" "mobile"; then
    echo "[PASS] Mobile type checking completed"
else
    echo "[FAIL] Mobile type checking failed"
fi

# Final result
echo ""
if [ "$OVERALL_SUCCESS" = true ]; then
    echo "[SUCCESS] All formatting and linting completed successfully!"
    exit 0
else
    echo "[FAILED] Some formatting/linting tasks failed. Check the output above for details."
    exit 1
fi

#!/bin/bash

# Code Formatting and Linting Script
# This script runs formatting and linting tools across all codebases

# Track overall success
OVERALL_SUCCESS=true

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

# Backend: Ruff format and lint
if run_command "backend ruff format" "python3 -m ruff format" "backend"; then
    echo "[PASS] Backend formatting completed"
else
    echo "[FAIL] Backend formatting failed"
fi

if run_command "backend ruff lint fix" "python3 -m ruff check --fix" "backend"; then
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

# Final result
echo ""
if [ "$OVERALL_SUCCESS" = true ]; then
    echo "[SUCCESS] All formatting and linting completed successfully!"
    exit 0
else
    echo "[FAILED] Some formatting/linting tasks failed. Check the output above for details."
    exit 1
fi

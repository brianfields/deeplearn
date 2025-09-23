#!/bin/bash

# Run Tests Script
# This script runs all test suites in the project with proper error handling

# Track overall success
OVERALL_SUCCESS=true

# Function to run a test and report result
run_test() {
    local test_name="$1"
    local test_command="$2"
    local test_dir="$3"

    echo "Running $test_name..."
    cd "$test_dir"

    if eval "$test_command"; then
        echo "[SUCCESS] $test_name completed"
        cd ..
        return 0
    else
        echo "[FAILED] $test_name failed"
        cd ..
        OVERALL_SUCCESS=false
        return 1
    fi
}

echo "Starting test suite..."

# Backend Unit Tests
if run_test "backend unit tests" "python3 scripts/run_unit.py" "backend"; then
    echo "[PASS] Backend unit tests passed"
else
    echo "[FAIL] Backend unit tests failed"
fi

# Frontend Unit Tests
if run_test "frontend unit tests" "npm run test" "mobile"; then
    echo "[PASS] Frontend unit tests passed"
else
    echo "[FAIL] Frontend unit tests failed"
fi

# Backend Integration Tests
if run_test "backend integration tests" "python3 scripts/run_integration.py" "backend"; then
    echo "[PASS] Backend integration tests passed"
else
    echo "[FAIL] Backend integration tests failed"
fi

# Frontend E2E Tests
echo "Starting required services for E2E (backend + iOS only)..."
./start.sh --no-admin --ios &
E2E_STACK_PID=$!

# Allow services to boot up
sleep 10

if run_test "frontend E2E tests" "npm run e2e:maestro" "mobile"; then
    echo "[PASS] Frontend E2E tests passed"
else
    echo "[FAIL] Frontend E2E tests failed"
fi

echo "Stopping E2E services..."
if [ -n "$E2E_STACK_PID" ]; then
    kill -TERM $E2E_STACK_PID 2>/dev/null || true
    wait $E2E_STACK_PID 2>/dev/null || true
fi

# Final result
echo ""
if [ "$OVERALL_SUCCESS" = true ]; then
    echo "[SUCCESS] All tests completed successfully!"
    exit 0
else
    echo "[FAILED] Some tests failed. Check the output above for details."
    exit 1
fi

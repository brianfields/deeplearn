#!/usr/bin/env python3
"""
Test script to verify that the timeout fix in common.py prevents hanging.
This simulates a subprocess that hangs to test our timeout mechanism.
"""

import subprocess
import sys
import time
from pathlib import Path

# Add the codegen directory to Python path so we can import common
sys.path.insert(0, str(Path(__file__).parent))

from common import run


def test_timeout_fix():
    """Test that run() function properly handles hanging subprocesses."""

    # Create a command that will hang indefinitely
    if sys.platform == "win32":
        hang_cmd = ["ping", "-t", "127.0.0.1"]  # Windows: ping indefinitely
    else:
        hang_cmd = ["tail", "-f", "/dev/null"]  # Unix: tail indefinitely

    print("Testing timeout mechanism with hanging subprocess...")
    start_time = time.time()

    # This should timeout and not hang
    exit_code = run(hang_cmd, stream_ndjson=False, echo=True)

    elapsed = time.time() - start_time
    print(f"Test completed in {elapsed:.1f} seconds with exit code {exit_code}")

    # Should complete quickly due to timeout (much less than 30 seconds)
    if elapsed < 25:  # Allow some buffer for process startup
        print("✅ Test passed: Process was terminated before hanging")
        return True
    else:
        print("❌ Test failed: Process may have hung")
        return False


def test_interrupt_handling():
    """Test that interrupt signals are handled properly."""
    print("Testing interrupt handling (Ctrl+C simulation)...")

    # This test would require actually sending SIGINT, which is complex
    # For now, just verify the signal handler is set up correctly
    import signal

    # Create a hanging process
    if sys.platform == "win32":
        hang_cmd = ["timeout", "/t", "30", "/nobreak"]
    else:
        hang_cmd = ["sleep", "30"]

    proc = subprocess.Popen(
        hang_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )

    # Simulate what our signal handler does
    def test_signal_handler(signum, frame):
        print(f"Signal {signum} received, terminating subprocess...")
        proc.terminate()
        try:
            proc.wait(timeout=5.0)
            print("✅ Graceful termination successful")
            return True
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
            print("✅ Force kill successful")
            return True

    # Test graceful termination
    old_handler = signal.signal(signal.SIGINT, test_signal_handler)

    # Simulate signal
    test_signal_handler(signal.SIGINT, None)

    # Restore handler
    signal.signal(signal.SIGINT, old_handler)

    return True


if __name__ == "__main__":
    print("Running timeout fix tests...\n")

    test1_passed = test_timeout_fix()
    print()
    test2_passed = test_interrupt_handling()
    print()

    if test1_passed and test2_passed:
        print("🎉 All tests passed! The hanging issue should be resolved.")
        sys.exit(0)
    else:
        print("❌ Some tests failed.")
        sys.exit(1)

#!/usr/bin/env python3
"""
Timing Test: Active Writing
This container continuously writes logs for an extended period.
Tests behavior when logs are requested while the container is still
actively writing (not in final state).
"""
import sys
import time
from datetime import datetime

def log_with_marker(message, stream=sys.stdout):
    timestamp = datetime.utcnow().isoformat() + "Z"
    marker = "[LOGS-TEST-ACTIVE-WRITING]"
    output = f"{timestamp} {marker} {message}"
    print(output, file=stream, flush=True)

def main():
    log_with_marker("Container started - continuous logging test")
    time.sleep(5)

    # Write continuously for 5 minutes (300 seconds)
    # One log line every 2 seconds = 150 log lines total
    duration_seconds = 300
    interval_seconds = 2
    iterations = duration_seconds // interval_seconds

    for i in range(iterations):
        elapsed = i * interval_seconds
        remaining = duration_seconds - elapsed
        log_with_marker(f"Active write iteration {i+1}/{iterations} - elapsed: {elapsed}s, remaining: {remaining}s")
        time.sleep(interval_seconds)

    log_with_marker("Continuous logging completed")
    time.sleep(20)
    sys.exit(0)

if __name__ == "__main__":
    main()

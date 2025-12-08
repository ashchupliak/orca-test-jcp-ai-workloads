#!/usr/bin/env python3
"""
Advanced Test: Rapid Output
This container generates logs as fast as possible without pauses.
Tests the system's ability to handle high-throughput log streams
and buffer management.
"""
import sys
from datetime import datetime

def log_with_marker(message, stream=sys.stdout):
    timestamp = datetime.utcnow().isoformat() + "Z"
    marker = "[LOGS-TEST-RAPID]"
    output = f"{timestamp} {marker} {message}"
    print(output, file=stream, flush=True)

def main():
    log_with_marker("Container started - rapid output test")

    # Generate 50,000 log lines as fast as possible (no sleep)
    # This tests buffer overflow, backpressure, and log loss scenarios
    LINE_COUNT = 50_000

    for i in range(LINE_COUNT):
        log_with_marker(f"Rapid line {i}: data data data data data data data")

        # Progress marker every 10k lines
        if i > 0 and i % 10_000 == 0:
            log_with_marker(f"*** PROGRESS: {i} lines written ***")

    log_with_marker(f"Rapid output completed - {LINE_COUNT} lines written")
    sys.exit(0)

if __name__ == "__main__":
    main()

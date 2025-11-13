#!/usr/bin/env python3
import sys
import time
from datetime import datetime

def log_with_marker(message, stream=sys.stdout):
    timestamp = datetime.utcnow().isoformat() + "Z"
    marker = "[LOGS-TEST-MULTI-STAGE]"
    output = f"{timestamp} {marker} {message}"
    print(output, file=stream, flush=True)

def main():
    log_with_marker("Container started")
    time.sleep(20)  # Give log-sender time to upload

    stages = [
        ("Setup", "Installing dependencies"),
        ("Build", "Compiling source code"),
        ("Test", "Running test suite"),
        ("Deploy", "Deploying application"),
        ("Cleanup", "Cleaning up resources")
    ]

    for i, (stage, action) in enumerate(stages, 1):
        log_with_marker(f"Stage {i}/5: {stage} started")
        log_with_marker(f"Stage {i}/5: {action}...")
        time.sleep(10)  # Longer delays between stages
        log_with_marker(f"Stage {i}/5: {stage} completed")

    log_with_marker("All stages completed successfully")
    time.sleep(10)
    log_with_marker("Container exiting")
    time.sleep(20)  # Final flush time
    sys.exit(0)

if __name__ == "__main__":
    main()

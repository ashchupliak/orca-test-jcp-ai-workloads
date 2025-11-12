#!/usr/bin/env python3
import sys
import time
from datetime import datetime

def log_with_marker(message, stream=sys.stdout):
    timestamp = datetime.utcnow().isoformat() + "Z"
    marker = "[LOGS-TEST-LONG-RUNNING]"
    output = f"{timestamp} {marker} {message}"
    print(output, file=stream, flush=True)

def main():
    log_with_marker("Container started - running for 60 seconds")

    total_iterations = 12
    sleep_interval = 5

    for i in range(total_iterations):
        progress = int((i + 1) / total_iterations * 100)
        log_with_marker(f"Progress update: {progress}% complete (iteration {i + 1}/{total_iterations})")

        if i < total_iterations - 1:
            time.sleep(sleep_interval)

    log_with_marker("Long running task completed")
    log_with_marker("Container exiting")
    sys.exit(0)

if __name__ == "__main__":
    main()

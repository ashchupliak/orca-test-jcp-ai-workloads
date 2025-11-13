#!/usr/bin/env python3
import sys
import time
from datetime import datetime

def log_with_marker(message, stream=sys.stdout):
    timestamp = datetime.utcnow().isoformat() + "Z"
    marker = "[LOGS-TEST-PROGRESS]"
    output = f"{timestamp} {marker} {message}"
    print(output, file=stream, flush=True)

def main():
    log_with_marker("Container started - showing progress bar")
    time.sleep(30)  # Give log-sender time to upload

    total_steps = 50
    marker = "[LOGS-TEST-PROGRESS]"

    for i in range(total_steps + 1):
        pct = int((i / total_steps) * 100)
        filled = int((i / total_steps) * 40)
        bar = "=" * filled + " " * (40 - filled)
        timestamp = datetime.utcnow().isoformat() + "Z"

        print(f"\r{timestamp} {marker} Downloading: [{bar}] {pct}%", end="", flush=True)
        time.sleep(0.5)  # Slower progress to give time for upload

    print()

    log_with_marker("Progress bar completed")
    time.sleep(10)
    log_with_marker("Container exiting")
    time.sleep(20)  # Final flush time
    sys.exit(0)

if __name__ == "__main__":
    main()

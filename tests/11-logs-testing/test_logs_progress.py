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

    total_steps = 50
    marker = "[LOGS-TEST-PROGRESS]"

    for i in range(total_steps + 1):
        pct = int((i / total_steps) * 100)
        filled = int((i / total_steps) * 40)
        bar = "=" * filled + " " * (40 - filled)
        timestamp = datetime.utcnow().isoformat() + "Z"

        print(f"\r{timestamp} {marker} Downloading: [{bar}] {pct}%", end="", flush=True)
        time.sleep(0.1)

    print()

    log_with_marker("Progress bar completed")
    log_with_marker("Container exiting")
    sys.exit(0)

if __name__ == "__main__":
    main()

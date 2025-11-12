#!/usr/bin/env python3
import sys
import json
from datetime import datetime

def log_json(level, message, **metadata):
    log_entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "level": level,
        "marker": "[LOGS-TEST-JSON]",
        "message": message,
        "metadata": metadata
    }
    print(json.dumps(log_entry), flush=True)

def main():
    log_json("INFO", "Container started", event="startup", version="1.0.0")
    log_json("INFO", "Processing data", event="processing", items=100, batch_size=10)
    log_json("DEBUG", "Debug information", event="debug", debug_flag=True, trace_id="abc123")
    log_json("WARN", "Warning condition detected", event="warning", threshold=0.8, current_value=0.85)
    log_json("INFO", "Data processing completed", event="completion", processed=100, failed=0, success_rate=1.0)
    log_json("INFO", "Container exiting", event="shutdown", exit_code=0)
    sys.exit(0)

if __name__ == "__main__":
    main()

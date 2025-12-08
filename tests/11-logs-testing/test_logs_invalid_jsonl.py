#!/usr/bin/env python3
"""
Edge Case Test: Invalid JSONL Content
This container outputs a mix of valid JSON, invalid JSON, and plain text.
Tests the parser's robustness and fallback behavior.
"""
import sys
import time
import json
from datetime import datetime

def log_with_marker(message, stream=sys.stdout):
    timestamp = datetime.utcnow().isoformat() + "Z"
    marker = "[LOGS-TEST-INVALID-JSONL]"
    output = f"{timestamp} {marker} {message}"
    print(output, file=stream, flush=True)

def main():
    log_with_marker("Container started - Invalid JSONL test")
    time.sleep(5)

    # Valid JSON
    log_with_marker("Valid JSON: " + json.dumps({"status": "started", "level": "info"}))
    time.sleep(2)

    # Invalid JSON - missing closing brace
    log_with_marker('Invalid JSON (unclosed): {"status": "running", "level": "info"')
    time.sleep(2)

    # Invalid JSON - trailing comma
    log_with_marker('Invalid JSON (trailing comma): {"status": "running", "level": "info",}')
    time.sleep(2)

    # Invalid JSON - single quotes
    log_with_marker("Invalid JSON (single quotes): {'status': 'running', 'level': 'info'}")
    time.sleep(2)

    # Plain text (not JSON at all)
    log_with_marker("Plain text: This is not JSON at all, just regular log output")
    time.sleep(2)

    # Valid JSON array
    log_with_marker("Valid JSON array: " + json.dumps([1, 2, 3, "test"]))
    time.sleep(2)

    # Invalid JSON - unquoted keys
    log_with_marker('Invalid JSON (unquoted keys): {status: "running", level: info}')
    time.sleep(2)

    # Valid nested JSON
    log_with_marker("Valid nested JSON: " + json.dumps({
        "event": "processing",
        "data": {"user": "test", "count": 42},
        "tags": ["important", "production"]
    }))
    time.sleep(2)

    # Invalid JSON - control characters
    log_with_marker('Invalid JSON (control chars): {"text": "line1\nline2\ttab"}')
    time.sleep(2)

    # Valid JSON (control chars escaped properly)
    log_with_marker("Valid JSON (escaped): " + json.dumps({"text": "line1\nline2\ttab"}))
    time.sleep(2)

    # Mixed line - starts with JSON, ends with text
    log_with_marker('Mixed: {"status": "ok"} - but then some plain text')
    time.sleep(2)

    # Empty JSON
    log_with_marker("Empty JSON object: {}")
    log_with_marker("Empty JSON array: []")
    time.sleep(2)

    # Very large JSON
    large_obj = {"data": "x" * 10000, "size": 10000}
    log_with_marker("Large JSON: " + json.dumps(large_obj))
    time.sleep(2)

    # JSON with Unicode
    log_with_marker("Unicode JSON: " + json.dumps({"emoji": "🚀", "text": "Привет мир"}))
    time.sleep(2)

    log_with_marker("Invalid JSONL test completed")
    time.sleep(20)
    sys.exit(0)

if __name__ == "__main__":
    main()

# Logs Testing Suite

Test scripts for validating the Orca logs endpoint functionality across various scenarios including basic operations, edge cases, timing issues, and advanced features.

## Test Scripts

### Original Tests (Basic Functionality)

### 1. test_logs_success.py
**Purpose**: Tests basic successful container execution
- Exit code: 0
- **Marker**: `[LOGS-TEST-SUCCESS]`

### 2. test_logs_failure.py
**Purpose**: Tests container failure scenarios
- Exit code: 1
- **Marker**: `[LOGS-TEST-FAILURE]`

### 3. test_logs_multi_stage.py
**Purpose**: Tests multi-stage pipeline operations
- Logs 5 stages: setup, build, test, deploy, cleanup
- Exit code: 0
- **Marker**: `[LOGS-TEST-MULTI-STAGE]`

### 4. test_logs_long_running.py
**Purpose**: Tests long-running container operations
- Runs for 60 seconds with progress updates every 5 seconds
- Exit code: 0
- **Marker**: `[LOGS-TEST-LONG-RUNNING]`

### 5. test_logs_crash.py
**Purpose**: Tests container crash/signal handling
- Sends SIGTERM to self
- **Marker**: `[LOGS-TEST-CRASH]`

### 6. test_logs_large_output.py
**Purpose**: Tests handling of large log volumes
- Generates 10,000 log lines
- Exit code: 0
- **Marker**: `[LOGS-TEST-LARGE-OUTPUT]`

### 7. test_logs_stderr.py
**Purpose**: Tests stderr-only output
- All output goes to stderr
- Exit code: 0
- **Marker**: `[LOGS-TEST-STDERR]`

### 8. test_logs_mixed.py
**Purpose**: Tests mixed stdout/stderr output
- Alternates between stdout and stderr (10 messages each)
- Exit code: 0
- **Marker**: `[LOGS-TEST-MIXED]`

### 9. test_logs_progress.py
**Purpose**: Tests progress bar with carriage return (`\r`)
- Shows downloading progress 0%-100%
- Exit code: 0
- **Marker**: `[LOGS-TEST-PROGRESS]`

### 10. test_logs_json.py
**Purpose**: Tests structured JSON logging
- Outputs JSON-formatted log entries with metadata
- Exit code: 0
- **Marker**: `[LOGS-TEST-JSON]`

---

### Edge Case Tests

### 11. test_logs_empty.py
**Purpose**: Tests empty log handling (zero bytes)
- Container produces NO output to stdout/stderr
- Exit code: 0
- **Marker**: None (silent execution)
- **Duration**: ~30 seconds

### 12. test_logs_large.py
**Purpose**: Tests extremely large logs (>100MB)
- Generates 500,000 log lines (~100-120MB)
- Tests memory safety, streaming, download timeouts
- Exit code: 0
- **Marker**: `[LOGS-TEST-LARGE]`
- **Duration**: 10-15 minutes
- **WARNING**: Resource intensive!

### 13. test_logs_unicode.py
**Purpose**: Tests Unicode and special characters
- Emoji, multi-byte UTF-8, RTL text, math symbols, currency symbols
- Multiple languages: Russian, Japanese, Arabic, Hebrew, Chinese, Korean
- Exit code: 0
- **Marker**: `[LOGS-TEST-UNICODE]`
- **Duration**: ~1 minute

### 14. test_logs_invalid_jsonl.py
**Purpose**: Tests parser robustness with invalid JSON
- Mix of valid JSON, invalid JSON, and plain text
- Unclosed braces, trailing commas, unquoted keys, control characters
- Exit code: 0
- **Marker**: `[LOGS-TEST-INVALID-JSONL]`
- **Duration**: ~1 minute

---

### Timing Issue Tests

### 15. test_logs_immediate_request.py
**Purpose**: Tests logs requested before ready
- 90-second delay before producing logs
- Tests polling behavior and eventual availability
- Exit code: 0
- **Marker**: `[LOGS-TEST-IMMEDIATE]`
- **Duration**: ~2.5 minutes

### 16. test_logs_active_writing.py
**Purpose**: Tests logs while container actively writing
- Continuous logging for 5 minutes (one line every 2 seconds)
- Tests real-time availability and file consistency
- Exit code: 0
- **Marker**: `[LOGS-TEST-ACTIVE-WRITING]`
- **Duration**: ~5.5 minutes

### 17. test_logs_quick_termination.py
**Purpose**: Tests race condition with quick termination
- Container exits in 3 seconds
- Tests log upload race condition
- Exit code: 0
- **Marker**: `[LOGS-TEST-QUICK-TERM]`
- **Duration**: ~5 seconds

---

### Advanced Feature Tests

### 18. test_logs_rapid_output.py
**Purpose**: Tests high-throughput rapid output
- 50,000 lines as fast as possible (no delays)
- Tests buffer management and log loss
- Exit code: 0
- **Marker**: `[LOGS-TEST-RAPID]`
- **Duration**: ~2 minutes

### 19. test_logs_binary_content.py
**Purpose**: Tests binary data and non-UTF-8 bytes
- Hex dumps, null bytes, binary representations
- All byte values 0x00-0xFF
- Exit code: 0
- **Marker**: `[LOGS-TEST-BINARY]`
- **Duration**: ~1 minute

## Running Tests

### Individual Test
```bash
python3 tests/11-logs-testing/test_logs_success.py
```

### All Tests
```bash
for script in tests/11-logs-testing/test_logs_*.py; do
    echo "Running $script"
    python3 "$script"
    echo "Exit code: $?"
    echo "---"
done
```

## Log Format

All logs follow this format:
```
YYYY-MM-DDTHH:MM:SS.ffffffZ [LOGS-TEST-{SCENARIO}] {message}
```

## Devcontainer

The `.devcontainer-logs-testing/` directory contains the devcontainer configuration for running these tests in a containerized environment.

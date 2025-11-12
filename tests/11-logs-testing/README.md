# Logs Testing Suite

Test scripts for validating the Orca logs endpoint functionality.

## Test Scripts

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

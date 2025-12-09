# Error Testing Scenarios

This directory documents test scenarios designed to trigger various error conditions in the Orca system to validate error visibility and user experience.

## Test Scenarios

### 1. Invalid Docker Image Reference
**Directory:** `.devcontainer-error-invalid-image/`
**Trigger:** References non-existent Docker image
**Expected Error:** Image pull failure
**Error Stage:** Container initialization (before build)
**What to Check:**
- Does user see error in GET `/api/environments/{id}` response?
- Is error message clear? (e.g., "Image not found: this-image-definitely-does-not-exist-12345:latest")
- Does environment status show FAILED?
- Are logs available via `/api/environments/{id}/logs`?

### 2. Dockerfile Build Failure
**Directory:** `.devcontainer-error-build-failure/`
**Trigger:** Dockerfile tries to install non-existent package
**Expected Error:** Docker build failure during RUN command
**Error Stage:** Container build (after image pull, before runtime)
**What to Check:**
- Does user see build error details?
- Is error message clear? (e.g., "Package not found: this-package-definitely-does-not-exist-xyz123")
- Can user see build logs?
- Does status show FAILED with helpful message?

### 3. PostStartCommand Failure
**Directory:** `.devcontainer-error-command-failure/`
**Trigger:** postStartCommand references non-existent command
**Expected Error:** Command execution failure after container starts
**Error Stage:** Post-start lifecycle (container running, command fails)
**What to Check:**
- Does user see command failure error?
- Is error message clear? (e.g., "Command not found: this-command-does-not-exist")
- Are worker logs available showing the failure?
- Does status transition from RUNNING → FAILED?

### 4. Missing Devcontainer.json
**Test via HTTP only** - Point config path to non-existent file
**Expected Error:** Config file not found
**Error Stage:** Job definition validation (before any container work)
**What to Check:**
- Does facade reject the request?
- Or does compute reject it?
- Is error message clear?
- Does user see helpful guidance?

### 5. Invalid Git Repository URL
**Test via HTTP** - Use malformed or non-existent repo URL
**Expected Error:** Git clone failure
**Error Stage:** Repository cloning (before devcontainer build)
**What to Check:**
- Does user see git clone error?
- Is error message clear? (e.g., "Repository not found: https://invalid...")
- Are git logs visible to user?
- Does status show FAILED?

### 6. Git Authentication Failure
**Test via HTTP** - Use private repo without credentials
**Expected Error:** Git authentication failure
**Error Stage:** Repository cloning
**What to Check:**
- Does user see authentication error?
- Is error message helpful? (e.g., "Authentication failed for https://...")
- Can user diagnose the issue?
- Does status show FAILED with clear message?

## Testing Methodology

1. **Create environment** using POST `/api/environments` with test devcontainer path
2. **Poll status** using GET `/api/environments/{id}` until final state
3. **Check error visibility:**
   - Is there an error message in the status response?
   - Is the error message clear and actionable?
   - Can user understand what went wrong?
4. **Check logs** using GET `/api/environments/{id}/logs`
   - Are logs available?
   - Do logs contain error details?
   - Is log content helpful for debugging?

## Findings Template

For each test scenario, document:

```markdown
### Scenario: [Name]

**Status:**
- Environment status: [PENDING/STARTING/RUNNING/FAILED/TERMINATED]
- Status details field: [present/absent]
- Error message: [exact text or "none"]

**Logs:**
- Worker logs available: [yes/no]
- Log contains error: [yes/no]
- Error details in logs: [clear/unclear/absent]

**User Experience:**
- Can user see what went wrong: [yes/no]
- Can user fix the issue: [yes/no/unclear]
- Error message clarity: [clear/vague/absent]

**Visibility Score:** [VISIBLE / PARTIALLY VISIBLE / INVISIBLE]

**Notes:** [Any additional observations]
```

## Expected Invisible Errors (From Code Analysis)

Based on the code investigation, these scenarios should have poor error visibility:

1. **Exposed Port Allocation Failure** - 500 error, no environment created
2. **Remote Terminal Allocation Failure** - 500 error, no environment created
3. **Unknown Environment Type** - Stuck in PENDING, no error message
4. **Unknown Config Type** - Silent fallback, unclear downstream error
5. **Unknown Git Auth Type** - Falls back to anonymous, confusing error
6. **Out-of-Order Status Updates** - Silently dropped, incorrect status
7. **Infinite Retry Loops** - Stuck in STARTING/PENDING forever

## Testing Against Nightly

```bash
BASE_URL="https://orca-server-nightly.labs.jb.gg"
TOKEN="eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0LXNlcnZpY2UiLCJ1c2VySWQiOiJ0ZXN0LXVzZXItaWQiLCJ1c2VyTmFtZSI6InRlc3QtdXNlciIsImlhdCI6MTc1NzUxMTI2MiwiZXhwIjoyMDcyODcxMjYyfQ.MQmTOPiBp22WKL476tn8o_97RzgoQcxY_-Gj35_9zyNW_7A7Np7Rqc_9TUa_AZSOub5o3WvS6K-eGVy91iCnug"

# Create environment
curl -X POST "$BASE_URL/api/environments" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "definition": {
      "type": "devcontainer",
      "git": {
        "repositories": [{
          "cloneUrl": "https://github.com/ashchupliak/orca-test-jcp-ai-workloads",
          "ref": "main"
        }]
      },
      "workspaceFolder": "orca-test-jcp-ai-workloads",
      "config": {
        "type": "path",
        "path": "orca-test-jcp-ai-workloads/.devcontainer-error-invalid-image/devcontainer.json"
      }
    }
  }'

# Get environment status
curl "$BASE_URL/api/environments/{id}" \
  -H "Authorization: Bearer $TOKEN"

# Get logs
curl "$BASE_URL/api/environments/{id}/logs" \
  -H "Authorization: Bearer $TOKEN"
```

## Success Criteria

An error is considered **VISIBLE** if:
1. Environment status shows FAILED (not stuck in PENDING/STARTING)
2. Status response includes clear error message in `statusDetails` or similar field
3. Error message helps user understand what went wrong
4. User can determine if issue is fixable or not

An error is considered **INVISIBLE** if:
1. Environment stuck in non-final status (PENDING/STARTING)
2. Environment shows FAILED but no error message
3. Error message is generic or technical (invariant violations)
4. User confused about what happened

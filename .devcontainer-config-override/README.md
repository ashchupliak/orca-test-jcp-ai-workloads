# Config Override Test Container

This directory contains devcontainer configurations for testing the **Config Override** feature (ORCA-150) in jcp-orca-facade.

## Purpose

These configurations are used to verify that:
1. The facade correctly passes config path/content to orca-compute
2. Orca-compute uses the specified config (not the default)
3. Environment variables and scripts from the specified config are executed

## Files

### `devcontainer.json`
Primary test configuration that sets:
- `CONFIG_SOURCE=config-override-path`
- `CONFIG_TYPE=path`
- `CONTAINER_NAME=config-override-test`
- Runs `init.sh` on container creation

### `alternative.json`
Alternative configuration to test multiple config files in the same directory:
- `CONFIG_SOURCE=alternative-config`
- `CONFIG_TYPE=path`
- `CONTAINER_NAME=config-override-alternative`
- `ALTERNATIVE_CONFIG=true`
- Runs `init-alternative.sh` on container creation

### `init.sh`
Initialization script that logs identifiable information:
- Prints all environment variables
- Shows Python version
- Lists workspace contents
- Prints test marker: `CONFIG_OVERRIDE_TEST: PASSED - Primary config loaded`

### `init-alternative.sh`
Alternative initialization script that logs:
- Same information as `init.sh`
- Plus: "This is the ALTERNATIVE configuration!"
- Test marker: `CONFIG_OVERRIDE_TEST: PASSED - Alternative config loaded`

## Usage

### In HTTP Tests

**Using devcontainer.json:**
```json
{
  "config": {
    "type": "path",
    "path": ".devcontainer-config-override/devcontainer.json"
  }
}
```

**Using alternative.json:**
```json
{
  "config": {
    "type": "path",
    "path": ".devcontainer-config-override/alternative.json"
  }
}
```

## Verification

After creating an environment with these configs, check the container logs:

```bash
# Get the pod name
kubectl get pods -n orca | grep <environment-id>

# Check logs for config markers
kubectl logs -n orca <pod-name> | grep "CONFIG_SOURCE"
# Expected: CONFIG_SOURCE: config-override-path (or alternative-config)

kubectl logs -n orca <pod-name> | grep "CONFIG_TYPE"
# Expected: CONFIG_TYPE: path

kubectl logs -n orca <pod-name> | grep "CONTAINER_NAME"
# Expected: CONTAINER_NAME: config-override-test (or config-override-alternative)

kubectl logs -n orca <pod-name> | grep "CONFIG_OVERRIDE_TEST"
# Expected: CONFIG_OVERRIDE_TEST: PASSED - Primary config loaded
#       (or: Alternative config loaded)
```

## Expected Log Output

### Primary Config (devcontainer.json)
```
==========================================
CONFIG OVERRIDE TEST - Primary Config
==========================================
CONFIG_SOURCE: config-override-path
CONFIG_TYPE: path
CONTAINER_NAME: config-override-test
TEST_MODE: devcontainer
==========================================
Container initialized successfully with PRIMARY config
Python version: Python 3.11.x
Current directory: /workspace
Workspace contents:
[... directory listing ...]
==========================================
CONFIG_OVERRIDE_TEST: PASSED - Primary config loaded
==========================================
```

### Alternative Config (alternative.json)
```
==========================================
CONFIG OVERRIDE TEST - Alternative Config
==========================================
CONFIG_SOURCE: alternative-config
CONFIG_TYPE: path
CONTAINER_NAME: config-override-alternative
TEST_MODE: devcontainer-alternative
ALTERNATIVE_CONFIG: true
==========================================
Container initialized successfully with ALTERNATIVE config
Python version: Python 3.11.x
Current directory: /workspace
This is the ALTERNATIVE configuration!
==========================================
CONFIG_OVERRIDE_TEST: PASSED - Alternative config loaded
==========================================
```

## Related Test Files

These containers are used by the following HTTP test files in jcp-orca-facade:
- `manual-playground/config-override-tests/config-path-tests.http`
  - Test #3: Uses `devcontainer.json`
  - Test #4: Uses `alternative.json`
  - Test #5: Uses `devcontainer.json` with workspaceFolder override

## Troubleshooting

### Container fails to start
- Check that the scripts have execute permissions: `chmod +x *.sh`
- Verify Python 3.11-slim image is available
- Check orca-compute logs for detailed error messages

### Scripts don't execute
- Verify `postCreateCommand` is correctly set in the JSON files
- Check that scripts exist in `/workspace/.devcontainer-config-override/`
- Ensure bash is available in the container (python:3.11-slim includes it)

### Environment variables not set
- Check that `remoteEnv` is correctly defined in the JSON
- Verify orca-compute passes remoteEnv to the container
- Check container logs to see which env vars are actually set

## Design Notes

### Why separate init scripts?
Having separate scripts makes it easier to identify which config was used:
- Different log messages
- Different test markers
- Different environment variable values

### Why these specific markers?
The markers (`CONFIG_SOURCE`, `CONFIG_TYPE`, etc.) are designed to be:
- Easy to grep in logs
- Unique enough to avoid false positives
- Descriptive of what they represent

### Image choice
Python 3.11-slim was chosen because:
- Lightweight (faster container start)
- Includes bash (needed for scripts)
- Common base image (good test coverage)
- Python version is easily verifiable

## Contributing

When modifying these configs:
1. Keep the environment variable names consistent
2. Update both `init.sh` and `init-alternative.sh` if changing log format
3. Test locally before committing
4. Update this README if adding new files or changing behavior
5. Ensure scripts remain executable (`chmod +x`)

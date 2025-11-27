#!/bin/bash
# Container validation script
# Validates all 22 containers are properly configured

echo "========================================="
echo "Container Configuration Validation"
echo "========================================="
echo ""

CONTAINERS=(
    ".devcontainer"
    ".devcontainer-agents"
    ".devcontainer-ai-tools"
    ".devcontainer-base"
    ".devcontainer-config-override"
    ".devcontainer-config-override-alt"
    ".devcontainer-databases"
    ".devcontainer-docker"
    ".devcontainer-dotnet"
    ".devcontainer-git"
    ".devcontainer-go"
    ".devcontainer-grazie"
    ".devcontainer-ide-test"
    ".devcontainer-java"
    ".devcontainer-javascript"
    ".devcontainer-lightweight-agent"
    ".devcontainer-logs-testing"
    ".devcontainer-mcp"
    ".devcontainer-php"
    ".devcontainer-python"
    ".devcontainer-ruby"
    ".devcontainer-rust"
)

TOTAL=${#CONTAINERS[@]}
PASSED=0
FAILED=0

for container in "${CONTAINERS[@]}"; do
    echo "Checking $container..."

    # Check Dockerfile exists
    if [ ! -f "$container/Dockerfile" ]; then
        echo "  ❌ Dockerfile missing"
        FAILED=$((FAILED + 1))
        continue
    fi

    # Check devcontainer.json exists
    if [ ! -f "$container/devcontainer.json" ]; then
        echo "  ❌ devcontainer.json missing"
        FAILED=$((FAILED + 1))
        continue
    fi

    # Check devcontainer.json uses Dockerfile
    if ! grep -q '"dockerFile": "Dockerfile"' "$container/devcontainer.json"; then
        echo "  ❌ devcontainer.json doesn't use Dockerfile"
        FAILED=$((FAILED + 1))
        continue
    fi

    # Check devcontainer.json has port mappings
    if ! grep -q '8000:8000' "$container/devcontainer.json"; then
        echo "  ❌ Port mappings missing"
        FAILED=$((FAILED + 1))
        continue
    fi

    # Check Dockerfile copies unified service
    if ! grep -q 'unified-service-java' "$container/Dockerfile"; then
        echo "  ❌ Dockerfile doesn't copy unified service"
        FAILED=$((FAILED + 1))
        continue
    fi

    # Check Dockerfile uses supervisor
    if ! grep -q 'supervisord' "$container/Dockerfile"; then
        echo "  ❌ Dockerfile doesn't use supervisor"
        FAILED=$((FAILED + 1))
        continue
    fi

    echo "  ✅ Configuration valid"
    PASSED=$((PASSED + 1))
done

echo ""
echo "========================================="
echo "Validation Summary"
echo "========================================="
echo "Total containers: $TOTAL"
echo "Passed: $PASSED"
echo "Failed: $FAILED"
echo ""

# Check unified service jar
if [ -f "unified-service-java/build/libs/unified-service.jar" ]; then
    JAR_SIZE=$(du -h unified-service-java/build/libs/unified-service.jar | cut -f1)
    echo "✅ Unified service jar exists ($JAR_SIZE)"
else
    echo "❌ Unified service jar missing"
fi

# Check supervisord config
if [ -f "common-config/supervisord.conf" ]; then
    echo "✅ Supervisor config exists"
else
    echo "❌ Supervisor config missing"
fi

echo ""
if [ $FAILED -eq 0 ]; then
    echo "✅ All containers are properly configured!"
    echo "Ready for testing via facade."
else
    echo "❌ Some containers have configuration issues."
    exit 1
fi

#!/bin/bash
# Run all tests or specific test categories

set -e

WORKSPACE_ROOT="/workspace"
TESTS_DIR="${WORKSPACE_ROOT}/tests"
OUTPUT_DIR="/tmp/test-results"

# Create output directory
mkdir -p "${OUTPUT_DIR}"

# Function to run a test script
run_test() {
    local test_script=$1
    local test_name=$(basename "$test_script" .py)
    local output_file="${OUTPUT_DIR}/${test_name}.json"

    echo "Running: $test_name..."
    if python3 "$test_script" --output "$output_file"; then
        echo "  ✓ PASSED: $test_name"
        return 0
    else
        echo "  ✗ FAILED: $test_name"
        return 1
    fi
}

# Parse arguments
CATEGORY=""
RUN_ALL=false
OUTPUT_FILE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --category)
            CATEGORY="$2"
            shift 2
            ;;
        --all)
            RUN_ALL=true
            shift
            ;;
        --output)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--category <category>] [--all] [--output <file>]"
            exit 1
            ;;
    esac
done

# Track results
TOTAL=0
PASSED=0
FAILED=0

echo "================================"
echo "Running Devcontainer Tests"
echo "================================"
echo "Output directory: ${OUTPUT_DIR}"
echo "================================"
echo ""

if [ "$RUN_ALL" = true ]; then
    echo "Running all test categories..."
    # Run tests in order
    for category_dir in "${TESTS_DIR}"/[0-9]*-*/; do
        if [ -d "$category_dir" ]; then
            category_name=$(basename "$category_dir")
            echo ""
            echo "Category: $category_name"
            echo "----------------------------"

            for test_script in "$category_dir"test_*.py; do
                if [ -f "$test_script" ]; then
                    ((TOTAL++))
                    if run_test "$test_script"; then
                        ((PASSED++))
                    else
                        ((FAILED++))
                    fi
                fi
            done
        fi
    done
elif [ -n "$CATEGORY" ]; then
    echo "Running category: $CATEGORY"
    echo "----------------------------"

    # Map category name to directory
    case $CATEGORY in
        environment)
            CATEGORY_DIR="${TESTS_DIR}/01-environment"
            ;;
        languages)
            CATEGORY_DIR="${TESTS_DIR}/02-languages"
            ;;
        git)
            CATEGORY_DIR="${TESTS_DIR}/03-git"
            ;;
        mcp)
            CATEGORY_DIR="${TESTS_DIR}/04-mcp"
            ;;
        agents)
            CATEGORY_DIR="${TESTS_DIR}/05-agents"
            ;;
        databases)
            CATEGORY_DIR="${TESTS_DIR}/06-databases"
            ;;
        docker)
            CATEGORY_DIR="${TESTS_DIR}/07-docker"
            ;;
        secrets)
            CATEGORY_DIR="${TESTS_DIR}/08-secrets"
            ;;
        grazie)
            CATEGORY_DIR="${TESTS_DIR}/10-grazie"
            ;;
        ai)
            CATEGORY_DIR="${TESTS_DIR}/90-ai-workloads"
            ;;
        *)
            echo "Unknown category: $CATEGORY"
            exit 1
            ;;
    esac

    if [ ! -d "$CATEGORY_DIR" ]; then
        echo "Category directory not found: $CATEGORY_DIR"
        exit 1
    fi

    for test_script in "$CATEGORY_DIR"/test_*.py; do
        if [ -f "$test_script" ]; then
            ((TOTAL++))
            if run_test "$test_script"; then
                ((PASSED++))
            else
                ((FAILED++))
            fi
        fi
    done
else
    echo "Error: Specify --all or --category <name>"
    echo "Available categories: environment, languages, git, mcp, agents, databases, docker, secrets, grazie, ai"
    exit 1
fi

echo ""
echo "================================"
echo "Test Results Summary"
echo "================================"
echo "Total:  $TOTAL"
echo "Passed: $PASSED"
echo "Failed: $FAILED"
echo "================================"

# Combine results if output file specified
if [ -n "$OUTPUT_FILE" ]; then
    echo "Combining results to: $OUTPUT_FILE"

    # Create combined JSON
    echo "{" > "$OUTPUT_FILE"
    echo "  \"summary\": {" >> "$OUTPUT_FILE"
    echo "    \"total\": $TOTAL," >> "$OUTPUT_FILE"
    echo "    \"passed\": $PASSED," >> "$OUTPUT_FILE"
    echo "    \"failed\": $FAILED" >> "$OUTPUT_FILE"
    echo "  }," >> "$OUTPUT_FILE"
    echo "  \"results\": [" >> "$OUTPUT_FILE"

    first=true
    for result_file in "${OUTPUT_DIR}"/*.json; do
        if [ -f "$result_file" ] && [ "$result_file" != "$OUTPUT_FILE" ]; then
            if [ "$first" = false ]; then
                echo "," >> "$OUTPUT_FILE"
            fi
            cat "$result_file" >> "$OUTPUT_FILE"
            first=false
        fi
    done

    echo "" >> "$OUTPUT_FILE"
    echo "  ]" >> "$OUTPUT_FILE"
    echo "}" >> "$OUTPUT_FILE"

    echo "Combined results saved to: $OUTPUT_FILE"
fi

# Exit with appropriate code
if [ $FAILED -gt 0 ]; then
    exit 1
else
    exit 0
fi

#!/bin/bash
set -e

echo "=========================================="
echo "AI Workload Health Check"
echo "=========================================="

echo ""
echo "1. Checking Python installation..."
python --version || { echo "❌ Python not found"; exit 1; }
echo "   ✅ Python installed"

echo ""
echo "2. Checking Python dependencies..."
python -c "import sys; print(f'   Python version: {sys.version}')"

# Check for common AI libraries
for lib in torch transformers numpy requests; do
    if python -c "import $lib" 2>/dev/null; then
        version=$(python -c "import $lib; print($lib.__version__)" 2>/dev/null || echo "unknown")
        echo "   ✅ $lib: $version"
    else
        echo "   ⚠️  $lib: Not installed (will be installed by requirements.txt)"
    fi
done

echo ""
echo "3. Checking CUDA availability..."
if python -c "import torch; print(f'   CUDA available: {torch.cuda.is_available()}')" 2>/dev/null; then
    python -c "import torch; print(f'   CUDA version: {torch.version.cuda if torch.cuda.is_available() else \"N/A\"}')" 2>/dev/null
else
    echo "   ⚠️  PyTorch not installed yet (will be installed)"
fi

echo ""
echo "4. Checking workspace directory..."
if [ -d "/workspace" ]; then
    echo "   ✅ Workspace directory exists"
    echo "   📁 Workspace contents:"
    ls -la /workspace | head -10
else
    echo "   ⚠️  Workspace directory not found"
fi

echo ""
echo "5. Checking model cache directory..."
if [ -d "${MODEL_CACHE_DIR:-/workspace/.cache/models}" ]; then
    echo "   ✅ Model cache directory exists"
else
    echo "   ℹ️  Model cache directory will be created on first use"
fi

echo ""
echo "6. Checking test scripts..."
if [ -d "tests" ]; then
    test_count=$(find tests -name "*.py" | wc -l)
    echo "   ✅ Found $test_count test script(s)"
    ls -1 tests/*.py 2>/dev/null || echo "   ℹ️  No test scripts found yet"
else
    echo "   ⚠️  Tests directory not found"
fi

echo ""
echo "=========================================="
echo "✅ Health check completed"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  - Install dependencies: pip install -r requirements.txt"
echo "  - Run tests: python tests/test_model_inference.py"
echo ""



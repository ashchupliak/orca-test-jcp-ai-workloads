# Orca AI Workload Test Repository

This repository contains test scripts and configurations for validating AI workloads in Orca devcontainer environments.

## Purpose

This repository is designed to test and validate:
- AI model loading and inference capabilities
- GPU-accelerated workloads
- API server functionality for AI services
- Concurrent request handling
- Performance benchmarking
- Secret management for AI credentials
- Environment health checks

## Repository Structure

```
.
├── .devcontainer/
│   └── devcontainer.json          # Container configuration
├── tests/
│   ├── test_model_inference.py    # Basic model inference test
│   ├── test_gpu_inference.py      # GPU-accelerated inference test
│   ├── test_concurrent_requests.py # Concurrent request test
│   ├── test_secret_management.py   # Secret handling test
│   └── benchmark.py                # Performance benchmark
├── scripts/
│   └── health-check.sh             # Environment health check
├── models/                         # Model files (gitignored)
├── requirements.txt                # Python dependencies
└── README.md                       # This file
```

## Quick Start

### 1. Environment Setup

The devcontainer will automatically:
- Install Python 3.11
- Install dependencies from `requirements.txt`
- Configure environment variables

### 2. Running Tests

**Basic Inference Test:**
```bash
python tests/test_model_inference.py
python tests/test_model_inference.py --output /tmp/results.json
```

**GPU Inference Test:**
```bash
python tests/test_gpu_inference.py
python tests/test_gpu_inference.py --output /tmp/gpu-results.json
```

**Concurrent Requests Test:**
```bash
python tests/test_concurrent_requests.py --num-requests 10 --api-url http://localhost:8000
```

**Performance Benchmark:**
```bash
python tests/benchmark.py --duration 300 --output /tmp/benchmark.json
```

**Health Check:**
```bash
./scripts/health-check.sh
```

### 3. Using with Orca Facade

This repository is configured to work with Orca Facade service. Use the HTTP test file:
`tests/src/test/kotlin/e2e/manual-playground/additional-tests/ai-workload-comprehensive-test.http`

## Test Aims

### 1. Basic Model Inference
- ✅ Load AI models (using HuggingFace transformers)
- ✅ Run inference on test prompts
- ✅ Validate output format and quality
- ✅ Measure inference latency

### 2. GPU-Accelerated Workloads
- ✅ Detect GPU availability
- ✅ Load models on GPU
- ✅ Execute GPU-accelerated inference
- ✅ Compare GPU vs CPU performance

### 3. API Server Testing
- ✅ Start AI API server
- ✅ Test API endpoints
- ✅ Handle concurrent requests
- ✅ Monitor API performance

### 4. Concurrent Requests
- ✅ Process multiple simultaneous requests
- ✅ Measure throughput
- ✅ Validate response consistency
- ✅ Monitor resource usage under load

### 5. Performance Benchmarking
- ✅ Measure CPU usage
- ✅ Monitor memory consumption
- ✅ Track inference latency
- ✅ Calculate throughput metrics

### 6. Secret Management
- ✅ Verify secrets are accessible in container
- ✅ Validate secrets are masked in API responses
- ✅ Test secret retrieval from environment variables

### 7. Health Checks
- ✅ Verify Python installation
- ✅ Check dependency availability
- ✅ Validate CUDA/GPU support
- ✅ Confirm workspace structure

## Environment Variables

The following environment variables can be configured:

- `MODEL_CACHE_DIR` - Directory for caching AI models (default: `/workspace/.cache/models`)
- `CUDA_VISIBLE_DEVICES` - GPU device ID (default: `0`)
- `PYTHONPATH` - Python module search path (default: `/workspace`)
- `API_HOST` - API server host (default: `0.0.0.0`)
- `API_PORT` - API server port (default: `8000`)
- `OPENAI_API_KEY` - OpenAI API key (if needed)
- `HUGGINGFACE_TOKEN` - HuggingFace token (if needed)

## Model Selection

Tests use lightweight models for speed:
- **gpt2** - Small, fast model for basic testing
- Models are downloaded on first run and cached for subsequent runs

For production testing, replace with your actual models.

## Performance Expectations

- **Model Loading**: 10-30 seconds (first run), cached afterwards
- **Inference Time**: < 1 second for small models
- **Concurrent Requests**: 10+ requests/second (depends on hardware)
- **Memory Usage**: 500MB - 2GB (depends on model size)

## Troubleshooting

### Model Download Fails
- Check internet connectivity
- Verify HuggingFace token if using private models
- Check disk space for model cache

### GPU Not Detected
- Verify GPU is available in container
- Check CUDA installation
- Verify `CUDA_VISIBLE_DEVICES` environment variable

### Import Errors
- Run `pip install -r requirements.txt`
- Check Python version (requires 3.8+)

### Permission Errors
- Ensure scripts are executable: `chmod +x scripts/*.sh`
- Check workspace directory permissions

## Contributing

When adding new tests:
1. Create test script in `tests/` directory
2. Add to HTTP test file if needed
3. Update this README with test description
4. Ensure tests are self-contained and produce JSON output

## License

This is a test repository for Orca Facade service testing.

## References

- [HuggingFace Transformers](https://huggingface.co/docs/transformers/)
- [PyTorch Documentation](https://pytorch.org/docs/)
- [Devcontainer Specification](https://containers.dev/)
- [Orca Facade Documentation](../../../README.md)

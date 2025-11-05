# Orca Devcontainer Test Repository

This repository contains comprehensive test scripts and configurations for validating Orca devcontainer environments for JetBrains developer workflows.

## Purpose

This repository is designed to test and validate:
- **Multi-language development environments** (Java, Python, JavaScript, Go, Kotlin, Rust, PHP, C#, Ruby)
- **Git operations** and GitHub CLI workflows
- **Database client connectivity** (PostgreSQL, MySQL, MongoDB, Redis)
- **Docker-in-Docker** support
- **Grazie AI integration** with staging environment
- **Agent tooling** for AI coding agents
- **Environment health** and system resources
- **Secrets management** for secure credential handling
- **AI/ML workloads** (optional, for AI-specific development tasks)

## Repository Structure

```
.
├── .devcontainer/
│   └── devcontainer.json                    # Multi-language devcontainer configuration
│
├── tests/
│   ├── 01-environment/                      # Basic environment validation
│   │   ├── test_health_check.py
│   │   └── test_system_resources.py
│   │
│   ├── 02-languages/                        # Programming language tests
│   │   ├── test_java.py
│   │   ├── test_python.py
│   │   └── test_javascript.py
│   │
│   ├── 03-git/                              # Git and GitHub workflows
│   │   ├── test_git_operations.py
│   │   └── test_github_cli.py
│   │
│   ├── 06-databases/                        # Database client tests
│   │   └── test_database_clients.py
│   │
│   ├── 07-docker/                           # Docker-in-Docker tests
│   │   └── test_docker_socket.py
│   │
│   ├── 10-grazie/                           # Grazie AI integration
│   │   ├── grazie_client.py                 # Grazie API client
│   │   └── test_grazie_staging.py           # Grazie staging test
│   │
│   ├── 90-ai-workloads/                     # AI/ML workload tests (optional)
│   │   ├── test_model_inference.py
│   │   ├── test_gpu_inference.py
│   │   └── benchmark.py
│   │
│   └── common/                              # Shared test utilities
│       ├── test_framework.py
│       └── __init__.py
│
├── scripts/
│   ├── run-all-tests.sh                     # Master test runner
│   └── install-tools.sh                     # Tool installation script
│
├── requirements.txt                         # Python dependencies
└── README.md                                # This file
```

## Quick Start

### Running Individual Tests

```bash
# Environment health check
python3 tests/01-environment/test_health_check.py --output /tmp/health-check.json

# Java development environment
python3 tests/02-languages/test_java.py --output /tmp/java-test.json

# Git operations
python3 tests/03-git/test_git_operations.py --output /tmp/git-test.json

# Grazie staging integration (requires GRAZIE_JWT_TOKEN)
export GRAZIE_JWT_TOKEN="your-token-here"
python3 tests/10-grazie/test_grazie_staging.py --output /tmp/grazie-test.json
```

### Running Test Categories

```bash
# Run all language tests
bash scripts/run-all-tests.sh --category languages --output /tmp/languages.json

# Run all git tests
bash scripts/run-all-tests.sh --category git --output /tmp/git-tests.json

# Run all database tests
bash scripts/run-all-tests.sh --category databases --output /tmp/databases.json

# Run all Docker tests
bash scripts/run-all-tests.sh --category docker --output /tmp/docker-tests.json

# Run Grazie tests
bash scripts/run-all-tests.sh --category grazie --output /tmp/grazie-tests.json
```

### Running Full Test Suite

```bash
# Run all tests
bash scripts/run-all-tests.sh --all --output /tmp/full-suite.json
```

### Using with Orca Facade

This repository is configured to work with the Orca Facade service. Use the HTTP test file:
- `tests/src/test/kotlin/e2e/manual-playground/additional-tests/comprehensive-devcontainer-test.http`

The HTTP tests will:
1. Provision an Orca environment from this repository
2. Execute test scripts inside the devcontainer
3. Collect logs and results
4. Terminate the environment when done

## Test Categories

### 1. Environment Health (01-environment/)
- ✅ System commands and utilities
- ✅ Environment variables
- ✅ File system accessibility
- ✅ CPU, memory, and disk resources

### 2. Programming Languages (02-languages/)
- ✅ **Java**: JDK, Maven, Gradle
- ✅ **Python**: Python 3, pip, virtualenv
- ✅ **JavaScript/Node.js**: Node, npm, npx
- ✅ **Go**: Go compiler and tools
- ✅ **Kotlin**: Kotlin compiler (via SDKMAN)
- ✅ **Rust**: Cargo and rustc
- ✅ **PHP**: PHP CLI and Composer
- ✅ **C#/.NET**: dotnet CLI
- ✅ **Ruby**: Ruby and bundler

### 3. Git & GitHub (03-git/)
- ✅ Git version control operations
- ✅ GitHub CLI (gh) commands
- ✅ Repository initialization, commits, and logs
- ✅ PR creation workflows (with authentication)

### 4. Database Clients (06-databases/)
- ✅ PostgreSQL client (psql)
- ✅ MySQL client (mysql)
- ✅ MongoDB shell (mongosh)
- ✅ Redis CLI (redis-cli)

### 5. Docker (07-docker/)
- ✅ Docker daemon access
- ✅ Docker socket availability
- ✅ Container execution

### 6. Grazie Integration (10-grazie/)
- ✅ Grazie API client
- ✅ Staging environment connectivity
- ✅ Chat query execution
- ✅ Response logging and validation

**Grazie Test Details:**
- Sends query: "please write a kotlin app that will do 2+2"
- Uses staging environment
- Requires `GRAZIE_JWT_TOKEN` environment variable
- Logs response clearly for worker logs inspection

### 7. AI/ML Workloads (90-ai-workloads/) - Optional
- ✅ AI model loading (HuggingFace transformers)
- ✅ GPU-accelerated inference
- ✅ Concurrent request handling
- ✅ Performance benchmarking

## Environment Variables

The following environment variables can be configured:

### Core Testing
- `PYTHONPATH` - Python module search path (default: `/workspace`)
- `TEST_MODE` - Test mode identifier (default: `devcontainer`)

### Grazie Integration
- `GRAZIE_JWT_TOKEN` - **Required** for Grazie tests - JWT token for Grazie staging authentication
- `USER_JWT_TOKEN` - Alternative name for JWT token

### AI Workloads (Optional)
- `MODEL_CACHE_DIR` - Directory for caching AI models (default: `/workspace/.cache/models`)
- `CUDA_VISIBLE_DEVICES` - GPU device ID (default: `0`)

### API Keys (Optional)
- `GITHUB_TOKEN` - GitHub token for PR operations
- `OPENAI_API_KEY` - OpenAI API key (if needed for AI tests)
- `HUGGINGFACE_TOKEN` - HuggingFace token (if needed for private models)

## Output Format

All tests produce JSON output with the following structure:

```json
{
  "status": "success",
  "test_type": "environment_health",
  "checks": [
    {
      "name": "bash_installed",
      "passed": true,
      "output": "bash version 5.1.16"
    }
  ],
  "metadata": {
    "environment": "devcontainer",
    "hostname": "container-xyz"
  },
  "timestamp": "2025-01-15T10:30:00",
  "duration_seconds": 2.5,
  "passed_checks": 10,
  "total_checks": 10
}
```

## Performance Expectations

- **Environment setup**: 2-5 minutes (first run)
- **Individual test execution**: 5-30 seconds
- **Full language suite**: 2-5 minutes
- **Grazie query**: 10-30 seconds (depending on model response time)
- **Full test suite**: 10-15 minutes

## Troubleshooting

### Test Failures

**No JWT token for Grazie tests:**
```bash
export GRAZIE_JWT_TOKEN="eyJhbGciOiJSUzUxMi..."
```

**Python dependencies missing:**
```bash
pip install -r requirements.txt
```

**Scripts not executable:**
```bash
chmod +x scripts/*.sh
chmod +x tests/*/*.py
```

### Common Issues

**Import errors in test scripts:**
- Ensure `PYTHONPATH=/workspace` is set
- Verify Python dependencies are installed

**Docker tests failing:**
- Verify Docker socket is mounted: `/var/run/docker.sock`
- Check Docker daemon is running

**Grazie client import errors:**
- Ensure `grazie_client.py` is in `tests/10-grazie/`
- Install dependencies: `pip install requests typing-extensions`

## Development Workflows

This repository supports the following typical JetBrains developer workflows:

1. **Backend Development**: Java/Spring Boot, Python/Django, Node.js/Express
2. **Frontend Development**: React, Vue, Angular with npm/yarn
3. **Mobile Development**: Kotlin for Android
4. **Database Development**: SQL client tools
5. **DevOps**: Docker, git, shell scripting
6. **AI/ML Development**: Python ML libraries, model inference
7. **Agent-Assisted Development**: AI coding agents, Grazie AI integration

## Integration with Orca Facade

The Orca Facade provisions ephemeral devcontainer environments from this repository:

1. **User Request** → "AI assistant, build feature X"
2. **Facade provisions environment** → Clones this repository, builds devcontainer
3. **Agent launches** → AI coding agent runs inside the container
4. **Development work** → Agent writes code, runs tests, commits changes
5. **Environment terminated** → Clean up after task completion

This test suite validates that these environments work correctly for all development scenarios.

## Contributing

When adding new tests:
1. Create test script in appropriate category directory
2. Follow `BaseTest` pattern from `common/test_framework.py`
3. Output JSON results to `/tmp/` for log collection
4. Update this README with test description
5. Add corresponding HTTP test in facade manual playground if needed

## License

This is a test repository for Orca Facade service testing.

## References

- [Orca Facade Documentation](../orca-server/README.md)
- [Devcontainer Specification](https://containers.dev/)
- [Grazie API Documentation](https://grazie-api.internal.jetbrains.com/docs)
- [JetBrains IDEs](https://www.jetbrains.com/ides/)

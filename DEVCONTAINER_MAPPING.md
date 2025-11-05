# Devcontainer Configuration Mapping

This document maps each test category to its optimized devcontainer configuration. Each devcontainer is minimal and contains only the dependencies needed for its specific tests.

## Benefits of Separate Devcontainers

✅ **Faster builds** - Each container only installs what it needs (2-5 min vs 15-20 min)
✅ **Smaller images** - Reduced disk space and memory usage
✅ **Better isolation** - Test-specific dependencies don't interfere
✅ **Parallel testing** - Different containers can build simultaneously
✅ **Easier debugging** - Smaller surface area for troubleshooting

## Devcontainer Configurations

### 1. Python Tests (.devcontainer-python/)

**Purpose:** Basic environment, health checks, secrets, networking tests

**Features:**
- Python 3.11
- Git
- requests library

**Tests:**
- `tests/01-environment/test_health_check.py`
- `tests/01-environment/test_system_resources.py`
- `tests/08-secrets/test_env_variables.py`
- `tests/09-networking/test_network_connectivity.py`

**HTTP Usage:**
```json
"configPath": "orca-test-jcp-ai-workloads/.devcontainer-python/devcontainer.json"
```

---

### 2. Java Tests (.devcontainer-java/)

**Purpose:** Java development environment testing

**Features:**
- Python 3.11 (test runner)
- Git
- Java 21
- Maven
- Gradle

**Tests:**
- `tests/02-languages/test_java.py`

**HTTP Usage:**
```json
"configPath": "orca-test-jcp-ai-workloads/.devcontainer-java/devcontainer.json"
```

---

### 3. JavaScript/Node.js Tests (.devcontainer-javascript/)

**Purpose:** JavaScript and Node.js environment testing

**Features:**
- Python 3.11 (test runner)
- Git
- Node.js LTS
- npm

**Tests:**
- `tests/02-languages/test_javascript.py`

**HTTP Usage:**
```json
"configPath": "orca-test-jcp-ai-workloads/.devcontainer-javascript/devcontainer.json"
```

---

### 4. Go Tests (.devcontainer-go/)

**Purpose:** Go development environment testing

**Features:**
- Python 3.11 (test runner)
- Git
- Go latest
- GOPATH configured

**Tests:**
- `tests/02-languages/test_go.py`

**HTTP Usage:**
```json
"configPath": "orca-test-jcp-ai-workloads/.devcontainer-go/devcontainer.json"
```

---

### 5. Rust Tests (.devcontainer-rust/)

**Purpose:** Rust development environment testing

**Features:**
- Python 3.11 (test runner)
- Git
- Rust (rustc, cargo)

**Tests:**
- `tests/02-languages/test_rust.py`

**HTTP Usage:**
```json
"configPath": "orca-test-jcp-ai-workloads/.devcontainer-rust/devcontainer.json"
```

---

### 6. .NET/C# Tests (.devcontainer-dotnet/)

**Purpose:** .NET and C# development environment testing

**Features:**
- Python 3.11 (test runner)
- Git
- .NET 8.0 SDK

**Tests:**
- `tests/02-languages/test_dotnet.py`

**HTTP Usage:**
```json
"configPath": "orca-test-jcp-ai-workloads/.devcontainer-dotnet/devcontainer.json"
```

---

### 7. Ruby Tests (.devcontainer-ruby/)

**Purpose:** Ruby development environment testing

**Features:**
- Python 3.11 (test runner)
- Git
- Ruby

**Tests:**
- `tests/02-languages/test_ruby.py`

**HTTP Usage:**
```json
"configPath": "orca-test-jcp-ai-workloads/.devcontainer-ruby/devcontainer.json"
```

---

### 8. PHP Tests (.devcontainer-php/)

**Purpose:** PHP development environment testing

**Features:**
- Python 3.11 (test runner)
- Git
- PHP

**Tests:**
- `tests/02-languages/test_php.py`

**HTTP Usage:**
```json
"configPath": "orca-test-jcp-ai-workloads/.devcontainer-php/devcontainer.json"
```

---

### 9. Git Operations Tests (.devcontainer-git/)

**Purpose:** Git and GitHub CLI functionality testing

**Features:**
- Python 3.11 (test runner)
- Git
- GitHub CLI (gh)

**Tests:**
- `tests/03-git/test_git_operations.py`
- `tests/03-git/test_github_cli.py`

**HTTP Usage:**
```json
"configPath": "orca-test-jcp-ai-workloads/.devcontainer-git/devcontainer.json"
```

---

### 10. MCP Tests (.devcontainer-mcp/)

**Purpose:** Model Context Protocol setup and functionality

**Features:**
- Python 3.11 (test runner)
- Git
- Node.js LTS
- MCP SDK

**Tests:**
- `tests/04-mcp/test_mcp_basic.py`

**HTTP Usage:**
```json
"configPath": "orca-test-jcp-ai-workloads/.devcontainer-mcp/devcontainer.json"
```

---

### 11. Grazie Tests (.devcontainer-grazie/)

**Purpose:** Grazie staging API integration testing

**Features:**
- Python 3.11
- Git
- requests library
- sseclient-py (for streaming)

**Tests:**
- `tests/10-grazie/test_grazie_staging.py`

**HTTP Usage:**
```json
"configPath": "orca-test-jcp-ai-workloads/.devcontainer-grazie/devcontainer.json"
```

---

### 12. Docker Tests (.devcontainer-docker/)

**Purpose:** Docker-in-Docker functionality testing

**Features:**
- Python 3.11 (test runner)
- Git
- Docker-in-Docker
- Docker socket mounted

**Tests:**
- `tests/07-docker/test_docker_socket.py`

**HTTP Usage:**
```json
"configPath": "orca-test-jcp-ai-workloads/.devcontainer-docker/devcontainer.json"
```

---

### 13. Database Client Tests (.devcontainer-databases/)

**Purpose:** Database client connectivity testing

**Features:**
- Python 3.11 (test runner)
- Git
- PostgreSQL client (psql)
- MySQL client (mysql)
- Redis CLI (redis-cli)
- MongoDB client (mongosh)

**Tests:**
- `tests/06-databases/test_database_clients.py`

**HTTP Usage:**
```json
"configPath": "orca-test-jcp-ai-workloads/.devcontainer-databases/devcontainer.json"
```

---

### 14. Agent Tests (.devcontainer-agents/)

**Purpose:** AI agent filesystem and command execution testing

**Features:**
- Python 3.11 (test runner)
- Git
- Standard Unix tools

**Tests:**
- `tests/05-agents/test_agent_filesystem.py`
- `tests/05-agents/test_agent_commands.py`

**HTTP Usage:**
```json
"configPath": "orca-test-jcp-ai-workloads/.devcontainer-agents/devcontainer.json"
```

---

## Complete HTTP Request Example

Here's a complete example of using a specific devcontainer:

```http
POST {{baseUrl}}/api/environments
Authorization: Bearer {{token}}
Content-Type: application/json
Accept: application/json

{
  "definition": {
    "type": "devcontainer",
    "git": {
      "repositories": [
        {
          "cloneUrl": "https://github.com/ashchupliak/orca-test-jcp-ai-workloads",
          "ref": "main"
        }
      ]
    },
    "env": [
      {
        "key": "TEST_TYPE",
        "value": "java_development",
        "description": "Test Java development tools"
      }
    ],
    "workspaceFolder": "orca-test-jcp-ai-workloads",
    "configPath": "orca-test-jcp-ai-workloads/.devcontainer-java/devcontainer.json",
    "runCmd": "python3 tests/02-languages/test_java.py --output /tmp/java-test.json"
  }
}
```

## Legacy Configuration

The original all-in-one devcontainer is still available at:
- `.devcontainer/devcontainer.json` - Full multilingual environment (heavy, 15-20 min build)
- `.devcontainer/devcontainer.minimal.json` - Minimal test configuration

## Quick Reference Table

| Test Category | Devcontainer Path | Build Time (approx) | Image Size (approx) |
|---------------|-------------------|---------------------|---------------------|
| Python/Basic | `.devcontainer-python/` | 2-3 min | 500 MB |
| Java | `.devcontainer-java/` | 4-5 min | 1.2 GB |
| JavaScript | `.devcontainer-javascript/` | 3-4 min | 700 MB |
| Go | `.devcontainer-go/` | 3-4 min | 800 MB |
| Rust | `.devcontainer-rust/` | 5-6 min | 1.5 GB |
| .NET | `.devcontainer-dotnet/` | 4-5 min | 1.1 GB |
| Ruby | `.devcontainer-ruby/` | 3-4 min | 600 MB |
| PHP | `.devcontainer-php/` | 3-4 min | 600 MB |
| Git/GitHub | `.devcontainer-git/` | 2-3 min | 500 MB |
| MCP | `.devcontainer-mcp/` | 3-4 min | 700 MB |
| Grazie | `.devcontainer-grazie/` | 2-3 min | 500 MB |
| Docker | `.devcontainer-docker/` | 4-5 min | 900 MB |
| Databases | `.devcontainer-databases/` | 3-4 min | 700 MB |
| Agents | `.devcontainer-agents/` | 2-3 min | 500 MB |
| **Legacy (all-in-one)** | `.devcontainer/` | **15-20 min** | **3-4 GB** |

## Testing Strategy

For comprehensive testing, you can now run tests in parallel:
- Each test category uses its own lightweight container
- Tests build and run faster
- Failures are easier to isolate and debug
- CI/CD pipelines can parallelize test execution

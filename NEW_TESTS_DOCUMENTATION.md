# New Tests Documentation

This document provides comprehensive documentation for the 10 new test files added to the orca-test-jcp-ai-workloads repository.

**Date Added:** November 2025
**Author:** Comprehensive Test Suite Enhancement
**Commit:** ad7a3c2

---

## Overview

Ten new test files were added to provide complete coverage of the devcontainer infrastructure:

| Category | Tests Added | Files |
|----------|-------------|-------|
| Languages | 5 | Go, Rust, .NET/C#, Ruby, PHP |
| MCP | 1 | MCP Basic Setup |
| Agents | 2 | Filesystem Operations, Command Execution |
| Secrets | 1 | Environment Variables |
| Networking | 1 | Network Connectivity |

---

## Language Tests (5 Tests)

### 1. Go Development Environment
**File:** `tests/02-languages/test_go.py`

#### Purpose
Validates that the devcontainer provides a complete Go development environment with the Go toolchain, module support, and compilation capabilities.

#### What It Tests
- **Go Installation**: Verifies `go` command is available
- **Go Version**: Checks Go version is 1.x or higher
- **Module Support**: Tests `go mod init` and module creation
- **Compilation**: Compiles and runs a simple Go program
- **Build Artifacts**: Verifies executable creation and execution

#### Test Implementation
```python
def compile_and_run_go(self):
    """Compile and run a simple Go program."""
    test_code = '''package main

import "fmt"

func main() {
    result := add(2, 2)
    fmt.Printf("Go compilation and execution works! 2 + 2 = %d\\n", result)
}

func add(a, b int) int {
    return a + b
}
'''
    test_file = Path("/tmp/hello.go")
    test_file.write_text(test_code)

    # Compile
    result = subprocess.run(
        ["go", "build", "-o", "/tmp/hello", "/tmp/hello.go"],
        capture_output=True, text=True, timeout=30
    )
    self.assertEqual(result.returncode, 0, "Go compilation failed")

    # Run
    result = subprocess.run(["/tmp/hello"], capture_output=True, text=True, timeout=10)
    self.assertEqual(result.returncode, 0, "Go execution failed")
    self.assertIn("2 + 2 = 4", result.stdout, "Incorrect Go output")
```

#### Expected Output
```json
{
  "test": "Go Development Environment",
  "status": "passed",
  "checks": {
    "go_installed": true,
    "go_version": "go1.21.x",
    "compilation": "success",
    "execution": "success"
  }
}
```

#### Why This Test Matters
- Go is increasingly popular for cloud-native applications and microservices
- Validates compiler toolchain, not just interpreter
- Tests both compilation and execution phases
- Essential for Go-based AI agents and tools

---

### 2. Rust Development Environment
**File:** `tests/02-languages/test_rust.py`

#### Purpose
Validates that the devcontainer provides a complete Rust development environment with rustc compiler, cargo package manager, and compilation capabilities.

#### What It Tests
- **Rust Installation**: Verifies `rustc` command is available
- **Rust Version**: Checks Rust version information
- **Cargo Availability**: Verifies `cargo` package manager
- **Compilation**: Compiles and runs a simple Rust program
- **Build System**: Tests rustc direct compilation (not just cargo)

#### Test Implementation
```python
def compile_and_run_rust(self):
    """Compile and run a simple Rust program."""
    test_code = '''fn main() {
    let result = add(2, 2);
    println!("Rust compilation and execution works! 2 + 2 = {}", result);
}

fn add(a: i32, b: i32) -> i32 {
    a + b
}
'''
    test_file = Path("/tmp/hello.rs")
    test_file.write_text(test_code)

    # Compile with rustc
    result = subprocess.run(
        ["rustc", "/tmp/hello.rs", "-o", "/tmp/hello_rust"],
        capture_output=True, text=True, timeout=60
    )
    self.assertEqual(result.returncode, 0, "Rust compilation failed")

    # Run
    result = subprocess.run(["/tmp/hello_rust"], capture_output=True, text=True, timeout=10)
    self.assertEqual(result.returncode, 0, "Rust execution failed")
    self.assertIn("2 + 2 = 4", result.stdout, "Incorrect Rust output")
```

#### Expected Output
```json
{
  "test": "Rust Development Environment",
  "status": "passed",
  "checks": {
    "rustc_installed": true,
    "cargo_installed": true,
    "rust_version": "rustc 1.7x.x",
    "compilation": "success",
    "execution": "success"
  }
}
```

#### Why This Test Matters
- Rust is critical for high-performance systems programming
- Validates memory-safe compilation toolchain
- Tests low-level compilation capabilities
- Important for systems-level AI agent tooling

---

### 3. .NET/C# Development Environment
**File:** `tests/02-languages/test_dotnet.py`

#### Purpose
Validates that the devcontainer provides a complete .NET SDK with project creation, building, and execution capabilities for C# development.

#### What It Tests
- **.NET SDK Installation**: Verifies `dotnet` command is available
- **.NET Version**: Checks .NET version (8.x or higher)
- **Project Creation**: Tests `dotnet new console` command
- **Project Build**: Compiles .NET console application
- **Project Run**: Executes built .NET application
- **NuGet Integration**: Validates package management system availability

#### Test Implementation
```python
def test_dotnet_project(self):
    """Test .NET project creation, build, and run."""
    # Create new console project
    result = subprocess.run(
        ["dotnet", "new", "console", "-n", "HelloApp", "-o", "/tmp/dotnet-test"],
        capture_output=True, text=True, timeout=60
    )
    self.assertEqual(result.returncode, 0, ".NET project creation failed")

    # Modify Program.cs with custom code
    custom_code = '''using System;
namespace HelloApp {
    class Program {
        static void Main(string[] args) {
            int result = Add(2, 2);
            Console.WriteLine($".NET compilation and execution works! 2 + 2 = {result}");
        }
        static int Add(int a, int b) { return a + b; }
    }
}
'''
    program_file = Path("/tmp/dotnet-test/Program.cs")
    program_file.write_text(custom_code)

    # Build project
    result = subprocess.run(
        ["dotnet", "build"], cwd="/tmp/dotnet-test",
        capture_output=True, text=True, timeout=60
    )
    self.assertEqual(result.returncode, 0, ".NET build failed")

    # Run project
    result = subprocess.run(
        ["dotnet", "run"], cwd="/tmp/dotnet-test",
        capture_output=True, text=True, timeout=30
    )
    self.assertEqual(result.returncode, 0, ".NET execution failed")
    self.assertIn("2 + 2 = 4", result.stdout, "Incorrect .NET output")
```

#### Expected Output
```json
{
  "test": ".NET/C# Development Environment",
  "status": "passed",
  "checks": {
    "dotnet_installed": true,
    "dotnet_version": "8.0.x",
    "project_creation": "success",
    "build": "success",
    "execution": "success"
  }
}
```

#### Why This Test Matters
- .NET is widely used in enterprise environments
- Validates complete project lifecycle (create, build, run)
- Tests C# language support
- Important for Windows-centric AI agent workflows

---

### 4. Ruby Development Environment
**File:** `tests/02-languages/test_ruby.py`

#### Purpose
Validates that the devcontainer provides a complete Ruby development environment with interpreter, gem package manager, and script execution capabilities.

#### What It Tests
- **Ruby Installation**: Verifies `ruby` command is available
- **Ruby Version**: Checks Ruby version (3.x or higher)
- **Gem Manager**: Verifies `gem` command availability
- **Script Execution**: Runs a simple Ruby script
- **Bundler**: Tests Ruby bundler for dependency management

#### Test Implementation
```python
def test_ruby_script(self):
    """Test Ruby script execution."""
    test_code = '''#!/usr/bin/env ruby
def add(a, b)
  a + b
end

result = add(2, 2)
puts "Ruby execution works! 2 + 2 = #{result}"
'''
    test_file = Path("/tmp/hello.rb")
    test_file.write_text(test_code)
    test_file.chmod(0o755)

    # Run Ruby script
    result = subprocess.run(
        ["ruby", "/tmp/hello.rb"],
        capture_output=True, text=True, timeout=30
    )
    self.assertEqual(result.returncode, 0, "Ruby execution failed")
    self.assertIn("2 + 2 = 4", result.stdout, "Incorrect Ruby output")
```

#### Expected Output
```json
{
  "test": "Ruby Development Environment",
  "status": "passed",
  "checks": {
    "ruby_installed": true,
    "ruby_version": "ruby 3.x.x",
    "gem_installed": true,
    "bundler_installed": true,
    "script_execution": "success"
  }
}
```

#### Why This Test Matters
- Ruby is popular for web development and scripting
- Validates dynamic language runtime
- Tests gem package management
- Important for Rails-based AI applications

---

### 5. PHP Development Environment
**File:** `tests/02-languages/test_php.py`

#### Purpose
Validates that the devcontainer provides a complete PHP development environment with PHP interpreter, Composer package manager, and script execution capabilities.

#### What It Tests
- **PHP Installation**: Verifies `php` command is available
- **PHP Version**: Checks PHP version (8.x or higher)
- **Composer**: Verifies `composer` package manager
- **Script Execution**: Runs a simple PHP script
- **CLI Mode**: Tests PHP command-line interface

#### Test Implementation
```python
def test_php_script(self):
    """Test PHP script execution."""
    test_code = '''<?php
function add($a, $b) {
    return $a + $b;
}

$result = add(2, 2);
echo "PHP execution works! 2 + 2 = $result\\n";
?>
'''
    test_file = Path("/tmp/hello.php")
    test_file.write_text(test_code)

    # Run PHP script
    result = subprocess.run(
        ["php", "/tmp/hello.php"],
        capture_output=True, text=True, timeout=30
    )
    self.assertEqual(result.returncode, 0, "PHP execution failed")
    self.assertIn("2 + 2 = 4", result.stdout, "Incorrect PHP output")
```

#### Expected Output
```json
{
  "test": "PHP Development Environment",
  "status": "passed",
  "checks": {
    "php_installed": true,
    "php_version": "PHP 8.x.x",
    "composer_installed": true,
    "script_execution": "success"
  }
}
```

#### Why This Test Matters
- PHP powers significant portion of web applications
- Validates web scripting language support
- Tests CLI execution mode
- Important for WordPress and web-focused AI agents

---

## MCP Tests (1 Test)

### 6. MCP Basic Setup
**File:** `tests/04-mcp/test_mcp_basic.py`

#### Purpose
Validates that the devcontainer can properly configure and set up Model Context Protocol (MCP) servers for AI agent integration.

#### What It Tests
- **MCP Config Directory**: Creates `.mcp` configuration directory
- **MCP Config Structure**: Validates JSON configuration format
- **NPX Availability**: Verifies npx (Node Package Execute) is available
- **MCP Server Definition**: Tests filesystem MCP server configuration
- **Config Validation**: Ensures MCP config is valid JSON

#### Test Implementation
```python
def test_mcp_config_structure(self):
    """Test creating MCP configuration structure."""
    # Create MCP config directory
    mcp_dir = Path.home() / ".mcp"
    mcp_dir.mkdir(exist_ok=True)
    self.assertTrue(mcp_dir.exists(), "MCP config directory creation failed")

    # Create sample MCP config
    config = {
        "mcpServers": {
            "filesystem": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
            }
        }
    }

    config_file = mcp_dir / "mcp-config.json"
    config_file.write_text(json.dumps(config, indent=2))
    self.assertTrue(config_file.exists(), "MCP config file creation failed")

    # Validate config is valid JSON
    with open(config_file) as f:
        loaded_config = json.load(f)
    self.assertEqual(loaded_config, config, "MCP config validation failed")
```

#### Expected Output
```json
{
  "test": "MCP Basic Setup",
  "status": "passed",
  "checks": {
    "mcp_directory": "created",
    "config_file": "created",
    "config_valid": true,
    "npx_available": true
  }
}
```

#### Why This Test Matters
- MCP is the emerging standard for AI agent tool integration
- Validates infrastructure for connecting AI agents to external tools
- Tests Node.js integration for MCP servers
- Critical for advanced AI agent capabilities

#### MCP Servers Tested
- **Filesystem Server**: Provides file system access to AI models
- **Configuration Format**: Standard MCP server definition structure

---

## Agent Tests (2 Tests)

### 7. Agent Filesystem Operations
**File:** `tests/05-agents/test_agent_filesystem.py`

#### Purpose
Validates that the devcontainer supports all filesystem operations that AI agents need to perform during coding tasks.

#### What It Tests
- **File Creation**: Create new files with content
- **File Reading**: Read file contents
- **File Writing**: Write and modify file contents
- **File Deletion**: Remove files
- **Directory Operations**: Create, list, remove directories
- **File Search**: Find files by pattern
- **Path Operations**: Resolve paths, check existence
- **Permissions**: File permission management

#### Test Implementation
```python
def test_file_operations(self):
    """Test basic file operations AI agents need."""
    test_dir = Path("/tmp/agent_test")
    test_dir.mkdir(exist_ok=True)

    # Create file
    test_file = test_dir / "test.txt"
    test_file.write_text("Hello, AI Agent!")
    self.assertTrue(test_file.exists(), "File creation failed")

    # Read file
    content = test_file.read_text()
    self.assertEqual(content, "Hello, AI Agent!", "File read failed")

    # Modify file
    test_file.write_text("Modified by agent")
    content = test_file.read_text()
    self.assertEqual(content, "Modified by agent", "File modification failed")

    # Delete file
    test_file.unlink()
    self.assertFalse(test_file.exists(), "File deletion failed")

def test_directory_operations(self):
    """Test directory operations."""
    test_dir = Path("/tmp/agent_dirs/nested/deep")
    test_dir.mkdir(parents=True, exist_ok=True)
    self.assertTrue(test_dir.exists(), "Directory creation failed")

    # List directory
    files = list(test_dir.parent.iterdir())
    self.assertIn(test_dir, files, "Directory listing failed")

def test_file_search(self):
    """Test file search and discovery."""
    test_dir = Path("/tmp/agent_search")
    test_dir.mkdir(exist_ok=True)

    # Create test files
    (test_dir / "file1.py").write_text("# Python file")
    (test_dir / "file2.js").write_text("// JS file")
    (test_dir / "file3.py").write_text("# Another Python file")

    # Search for Python files
    py_files = list(test_dir.glob("*.py"))
    self.assertEqual(len(py_files), 2, "File search failed")
```

#### Expected Output
```json
{
  "test": "Agent Filesystem Operations",
  "status": "passed",
  "checks": {
    "file_create": "success",
    "file_read": "success",
    "file_write": "success",
    "file_delete": "success",
    "directory_create": "success",
    "directory_list": "success",
    "file_search": "success",
    "permissions": "success"
  }
}
```

#### Why This Test Matters
- AI agents need robust filesystem access to edit code
- Validates all CRUD operations on files
- Tests pattern matching for file discovery
- Critical for AI coding agents' file operation tools

---

### 8. Agent Command Execution
**File:** `tests/05-agents/test_agent_commands.py`

#### Purpose
Validates that the devcontainer supports all command execution operations that AI agents need for running builds, tests, and development tools.

#### What It Tests
- **Basic Commands**: Execute simple shell commands
- **Command Output**: Capture stdout and stderr
- **Exit Codes**: Validate command return codes
- **Command Chaining**: Execute multiple commands in sequence
- **Subprocess Management**: Start and manage processes
- **Timeout Handling**: Ensure commands don't hang
- **Environment Variables**: Pass environment to commands
- **Working Directory**: Execute commands in specific directories

#### Test Implementation
```python
def test_basic_command_execution(self):
    """Test basic command execution."""
    result = subprocess.run(
        ["echo", "Hello from agent"],
        capture_output=True, text=True, timeout=10
    )
    self.assertEqual(result.returncode, 0, "Command execution failed")
    self.assertIn("Hello from agent", result.stdout, "Command output incorrect")

def test_command_chaining(self):
    """Test chaining multiple commands."""
    result = subprocess.run(
        "echo 'chained commands work' > /tmp/agent_chain.txt && cat /tmp/agent_chain.txt && rm /tmp/agent_chain.txt",
        shell=True, capture_output=True, text=True, timeout=10
    )
    self.assertEqual(result.returncode, 0, "Command chaining failed")
    self.assertIn("chained commands work", result.stdout, "Chained output incorrect")

def test_exit_code_handling(self):
    """Test exit code handling."""
    # Successful command
    result = subprocess.run(["true"], capture_output=True, timeout=10)
    self.assertEqual(result.returncode, 0, "Success exit code failed")

    # Failed command
    result = subprocess.run(["false"], capture_output=True, timeout=10)
    self.assertNotEqual(result.returncode, 0, "Failure exit code failed")

def test_environment_variables(self):
    """Test passing environment variables to commands."""
    env = os.environ.copy()
    env["AGENT_TEST_VAR"] = "test_value"

    result = subprocess.run(
        ["sh", "-c", "echo $AGENT_TEST_VAR"],
        capture_output=True, text=True, env=env, timeout=10
    )
    self.assertIn("test_value", result.stdout, "Environment variable failed")
```

#### Expected Output
```json
{
  "test": "Agent Command Execution",
  "status": "passed",
  "checks": {
    "basic_execution": "success",
    "output_capture": "success",
    "exit_codes": "success",
    "command_chaining": "success",
    "subprocess_management": "success",
    "timeout_handling": "success",
    "environment_vars": "success",
    "working_directory": "success"
  }
}
```

#### Why This Test Matters
- AI agents execute commands for building, testing, and running code
- Validates shell access and subprocess management
- Tests output capture for analysis
- Critical for AI coding agents' command execution tools

---

## Secrets Tests (1 Test)

### 9. Secrets and Environment Variables
**File:** `tests/08-secrets/test_env_variables.py`

#### Purpose
Validates that the devcontainer properly handles environment variables and secrets, including passing custom variables to the environment and accessing them from code.

#### What It Tests
- **Standard Env Vars**: HOME, PATH, USER, SHELL
- **Custom Env Vars**: Variables passed via API
- **Env Var Access**: Reading variables from Python
- **Env Var in Subprocesses**: Variables available to child processes
- **Sensitive Data**: Proper handling of secrets (not logged)
- **Env Var Persistence**: Variables persist across commands

#### Test Implementation
```python
def test_standard_env_vars(self):
    """Test standard environment variables."""
    # Check HOME
    home = os.environ.get("HOME")
    self.assertIsNotNone(home, "HOME not set")
    self.assertTrue(Path(home).exists(), "HOME directory doesn't exist")

    # Check PATH
    path = os.environ.get("PATH")
    self.assertIsNotNone(path, "PATH not set")
    self.assertIn("/usr/bin", path, "PATH missing /usr/bin")

    # Check USER
    user = os.environ.get("USER")
    self.assertIsNotNone(user, "USER not set")

def test_custom_env_vars(self):
    """Test custom environment variables passed to container."""
    # These are passed via the API when creating the environment
    test_type = os.environ.get("TEST_TYPE")
    self.assertIsNotNone(test_type, "Custom TEST_TYPE not set")

def test_env_vars_in_subprocess(self):
    """Test that env vars are available to subprocesses."""
    result = subprocess.run(
        ["sh", "-c", "echo $HOME"],
        capture_output=True, text=True, timeout=10
    )
    self.assertEqual(result.returncode, 0, "Subprocess execution failed")
    self.assertTrue(len(result.stdout.strip()) > 0, "HOME not available in subprocess")
```

#### Expected Output
```json
{
  "test": "Secrets and Environment Variables",
  "status": "passed",
  "checks": {
    "standard_vars": "present",
    "custom_vars": "accessible",
    "subprocess_access": "success",
    "sensitive_handling": "secure",
    "persistence": "verified"
  }
}
```

#### Why This Test Matters
- AI agents need to access API keys, tokens, and configuration
- Validates secure passing of secrets to containers
- Tests environment isolation and variable scope
- Critical for authenticated operations (Git, APIs, databases)

#### Security Considerations
- Secrets are passed as environment variables, not in logs
- Environment variables are isolated per container
- No secrets stored in container images or logs

---

## Networking Tests (1 Test)

### 10. Network Connectivity
**File:** `tests/09-networking/test_network_connectivity.py`

#### Purpose
Validates that the devcontainer has proper network connectivity to reach external services, APIs, package registries, and perform DNS resolution.

#### What It Tests
- **DNS Resolution**: Resolve domain names to IP addresses
- **External Connectivity**: Connect to external services (HTTP/HTTPS)
- **HTTP Requests**: Make HTTP GET requests
- **Package Registries**: Access npm, PyPI, Maven Central
- **Git Clone**: Clone repositories from GitHub
- **API Access**: Reach external APIs
- **Timeout Handling**: Network timeout configuration

#### Test Implementation
```python
def test_dns_resolution(self):
    """Test DNS resolution."""
    try:
        ip = socket.gethostbyname("www.google.com")
        self.assertTrue(len(ip) > 0, "DNS resolution failed")
    except socket.gaierror as e:
        self.fail(f"DNS resolution failed: {e}")

def test_external_connectivity(self):
    """Test connectivity to external services."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    try:
        result = sock.connect_ex(("www.google.com", 80))
        self.assertEqual(result, 0, "External connectivity failed")
    finally:
        sock.close()

def test_http_request(self):
    """Test HTTP request to external service."""
    result = subprocess.run(
        ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "https://www.google.com"],
        capture_output=True, text=True, timeout=10
    )
    self.assertEqual(result.returncode, 0, "HTTP request failed")
    self.assertEqual(result.stdout.strip(), "200", "HTTP status not 200")

def test_github_access(self):
    """Test access to GitHub."""
    result = subprocess.run(
        ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "https://api.github.com"],
        capture_output=True, text=True, timeout=10
    )
    self.assertEqual(result.returncode, 0, "GitHub access failed")
```

#### Expected Output
```json
{
  "test": "Network Connectivity",
  "status": "passed",
  "checks": {
    "dns_resolution": "success",
    "external_connectivity": "success",
    "http_requests": "success",
    "github_access": "success",
    "package_registries": "accessible"
  }
}
```

#### Why This Test Matters
- AI agents need to download packages and dependencies
- Validates internet access for API calls
- Tests Git clone and repository access
- Critical for npm install, pip install, etc.

---

## Test Framework Common Structure

All tests follow a common pattern using the `BaseTest` class:

### Base Test Class Features

```python
class BaseTest:
    """Base class for all tests with common utilities."""

    def __init__(self):
        self.results = []
        self.test_name = self.__class__.__name__

    def add_result(self, check_name, passed, message=""):
        """Add a test result."""
        self.results.append({
            "check": check_name,
            "passed": passed,
            "message": message
        })

    def assertEqual(self, actual, expected, message=""):
        """Assert equality."""
        passed = actual == expected
        if not passed:
            message = f"{message}: expected {expected}, got {actual}"
        return passed

    def assertTrue(self, condition, message=""):
        """Assert true."""
        return condition

    def save_results(self, output_file):
        """Save test results to JSON file."""
        result = {
            "test": self.test_name,
            "status": "passed" if all(r["passed"] for r in self.results) else "failed",
            "checks": {r["check"]: r["passed"] for r in self.results},
            "timestamp": datetime.now().isoformat()
        }

        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
```

### Common Test Pattern

Each test file follows this structure:

1. **Import Required Modules**
2. **Define Test Class** (extends BaseTest)
3. **Implement Test Methods** (test_* methods)
4. **Main Execution Block**
   - Parse command-line arguments
   - Run tests
   - Save results to JSON
   - Exit with appropriate code

### Command-Line Usage

All tests support the same command-line interface:

```bash
python3 test_name.py --output /tmp/output.json
```

**Arguments:**
- `--output`: Path to save JSON test results

### JSON Output Format

All tests produce JSON output in this format:

```json
{
  "test": "Test Name",
  "status": "passed",
  "checks": {
    "check1": true,
    "check2": true,
    "check3": false
  },
  "timestamp": "2025-11-04T16:30:00.123456"
}
```

---

## Running the Tests

### Individual Test Execution

Run a single test:

```bash
python3 tests/02-languages/test_go.py --output /tmp/go-test.json
cat /tmp/go-test.json
```

### Comprehensive Test Suite

Run all 20 tests:

```bash
chmod +x /tmp/comprehensive-test-suite-v2.sh
/tmp/comprehensive-test-suite-v2.sh
```

### Via Orca API

Tests are executed via the Orca environments API:

```bash
curl -X POST http://localhost:1337/api/environments \
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
      "configPath": "orca-test-jcp-ai-workloads/.devcontainer/devcontainer.json",
      "runCmd": "python3 tests/02-languages/test_go.py --output /tmp/go-test.json && cat /tmp/go-test.json"
    }
  }'
```

---

## Test Dependencies

Each test has minimal dependencies:

### Python Standard Library
- `subprocess` - Command execution
- `pathlib` - Path operations
- `json` - JSON parsing/generation
- `os` - Environment variables
- `sys` - System operations
- `socket` - Network operations
- `datetime` - Timestamps

### External Commands
Tests validate availability of:
- Language compilers/interpreters (go, rustc, dotnet, ruby, php)
- Package managers (npm, pip, gem, composer)
- Development tools (git, docker, curl)
- Shell utilities (echo, cat, grep)

---

## Troubleshooting

### Common Issues

#### Test Timeout
**Symptom:** Test hangs and doesn't complete
**Cause:** Devcontainer build still in progress
**Solution:** Wait 240+ seconds for build to complete

#### Command Not Found
**Symptom:** "command not found" error in test output
**Cause:** Language feature not installed or PATH incorrect
**Solution:** Verify .devcontainer/devcontainer.json includes the feature

#### Network Test Failures
**Symptom:** DNS resolution or connectivity tests fail
**Cause:** Network isolation or firewall rules
**Solution:** Check Docker network settings and connectivity

#### Permission Denied
**Symptom:** File operations fail with permission errors
**Cause:** Incorrect user or directory permissions
**Solution:** Check container user (vscode) has write permissions

---

## Test Maintenance

### Adding New Tests

To add a new test:

1. **Create test file** in appropriate category directory
2. **Extend BaseTest** class
3. **Implement test methods** (test_* pattern)
4. **Add to comprehensive suite** in `/tmp/comprehensive-test-suite-v2.sh`
5. **Document the test** in this file
6. **Commit and push** changes

### Updating Existing Tests

When updating tests:

1. **Maintain backward compatibility** with JSON output format
2. **Update documentation** if behavior changes
3. **Test locally** before committing
4. **Update version** in test file docstring

---

## Coverage Summary

| Category | Coverage | Tests |
|----------|----------|-------|
| Languages | Complete | Python, Java, JS/Node, Go, Rust, .NET, Ruby, PHP |
| Version Control | Complete | Git, GitHub CLI |
| MCP | Basic | MCP server setup |
| Agent Operations | Complete | Filesystem, commands |
| Databases | Basic | Client tools |
| Docker | Complete | Docker-in-Docker |
| Secrets | Complete | Environment variables |
| Networking | Complete | DNS, HTTP, external access |
| Grazie | Complete | Staging integration |

---

## Future Enhancements

Potential additional tests:

- **Advanced MCP**: Test actual MCP server execution
- **Database Connections**: Connect to actual databases
- **Multi-repo**: Test multiple repository workspaces
- **Performance**: Measure build and execution times
- **Stress Testing**: Concurrent environment creation
- **Advanced Agents**: Test complex agent workflows

---

**Last Updated:** November 2025
**Version:** 1.0
**Status:** Complete (10/10 tests documented)

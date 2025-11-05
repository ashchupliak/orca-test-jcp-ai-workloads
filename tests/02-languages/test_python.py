#!/usr/bin/env python3
"""
Python development environment test.
Validates Python, pip, and real-world web API development workflow.
Creates a Flask API, writes tests, and validates functionality.
"""

import sys
import subprocess
import time
from pathlib import Path

# Add parent directory to path to import common utilities
sys.path.insert(0, str(Path(__file__).parent.parent))

from common.test_framework import BaseTest, main_template


class PythonTest(BaseTest):
    """Test Python development tools with realistic workflow."""

    def __init__(self):
        super().__init__("python_web_api")
        self.work_dir = Path("/tmp/python_test_app")

    def run(self):
        """Run comprehensive Python development workflow."""
        print("Testing Python development environment with Flask API...")

        # Phase 1: Check basic tools
        self.check_command_exists("python3", "Python 3")
        success, version = self.check_version("python3")
        if success:
            self.result.set_metadata("python_version", version.split()[1] if len(version.split()) > 1 else version)

        self.check_command_exists("pip3", "pip3")
        success, version = self.check_version("pip3")
        if success:
            self.result.set_metadata("pip_version", version.split()[1] if 'pip' in version else version)

        # Phase 2: Install dependencies
        self.install_dependencies()

        # Phase 3: Create Flask application
        self.create_flask_app()

        # Phase 4: Create test suite
        self.create_test_suite()

        # Phase 5: Run tests
        self.run_tests()

        # Phase 6: Start server and test endpoints
        self.test_api_endpoints()

        # Cleanup
        self.cleanup()

        return self.result

    def install_dependencies(self):
        """Install Flask and pytest from PyPI."""
        print("Installing Flask and pytest...")

        def install():
            cmd = "pip3 install --user flask pytest requests"
            success, output, error = self.run_command(cmd, timeout=120)
            return success, output, error

        (success, output, error), duration = self.measure_time(
            "pip_install_time",
            install
        )

        self.result.add_check(
            name="pip_install_dependencies",
            passed=success,
            output=f"Installed in {duration:.2f}s",
            error=error if not success else None
        )

        if success:
            # Validate Flask can be imported
            success, output, error = self.run_command("python3 -c 'import flask; print(flask.__version__)'")
            self.result.add_check(
                name="flask_import",
                passed=success,
                output=f"Flask version: {output}" if success else None,
                error=error if not success else None
            )
            if success:
                self.result.set_metadata("flask_version", output)

    def create_flask_app(self):
        """Create a realistic Flask REST API."""
        print("Creating Flask application...")

        self.work_dir.mkdir(parents=True, exist_ok=True)

        app_code = '''"""
Flask REST API for testing.
Provides endpoints for user management.
"""
from flask import Flask, jsonify, request

app = Flask(__name__)

# In-memory data store
users = {
    1: {"id": 1, "name": "Alice", "email": "alice@example.com"},
    2: {"id": 2, "name": "Bob", "email": "bob@example.com"}
}
next_id = 3


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "service": "user-api"}), 200


@app.route('/users', methods=['GET'])
def get_users():
    """Get all users."""
    return jsonify({"users": list(users.values())}), 200


@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Get a specific user."""
    if user_id in users:
        return jsonify(users[user_id]), 200
    return jsonify({"error": "User not found"}), 404


@app.route('/users', methods=['POST'])
def create_user():
    """Create a new user."""
    global next_id
    data = request.get_json()

    if not data or 'name' not in data or 'email' not in data:
        return jsonify({"error": "Missing name or email"}), 400

    user = {
        "id": next_id,
        "name": data['name'],
        "email": data['email']
    }
    users[next_id] = user
    next_id += 1

    return jsonify(user), 201


@app.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """Update an existing user."""
    if user_id not in users:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json()
    if 'name' in data:
        users[user_id]['name'] = data['name']
    if 'email' in data:
        users[user_id]['email'] = data['email']

    return jsonify(users[user_id]), 200


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)
'''

        app_file = self.work_dir / "app.py"
        try:
            app_file.write_text(app_code)
            self.result.add_check(
                name="create_flask_app",
                passed=True,
                output=f"Created {app_file}"
            )
            self.result.add_validation("app_file", str(app_file))
        except Exception as e:
            self.result.add_check(
                name="create_flask_app",
                passed=False,
                error=str(e)
            )

    def create_test_suite(self):
        """Create pytest test suite for the Flask API."""
        print("Creating pytest test suite...")

        test_code = '''"""
Test suite for Flask user API.
"""
import pytest
import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app import app, users


@pytest.fixture
def client():
    """Create test client."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

    # Reset users after each test
    users.clear()
    users[1] = {"id": 1, "name": "Alice", "email": "alice@example.com"}
    users[2] = {"id": 2, "name": "Bob", "email": "bob@example.com"}


def test_health_endpoint(client):
    """Test health check endpoint."""
    response = client.get('/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'healthy'
    assert data['service'] == 'user-api'


def test_get_all_users(client):
    """Test getting all users."""
    response = client.get('/users')
    assert response.status_code == 200
    data = response.get_json()
    assert 'users' in data
    assert len(data['users']) == 2


def test_get_user_by_id(client):
    """Test getting a specific user."""
    response = client.get('/users/1')
    assert response.status_code == 200
    data = response.get_json()
    assert data['id'] == 1
    assert data['name'] == 'Alice'


def test_get_nonexistent_user(client):
    """Test getting a user that doesn't exist."""
    response = client.get('/users/999')
    assert response.status_code == 404
    data = response.get_json()
    assert 'error' in data


def test_create_user(client):
    """Test creating a new user."""
    new_user = {
        "name": "Charlie",
        "email": "charlie@example.com"
    }
    response = client.post('/users', json=new_user)
    assert response.status_code == 201
    data = response.get_json()
    assert data['name'] == 'Charlie'
    assert data['email'] == 'charlie@example.com'
    assert 'id' in data


def test_create_user_invalid(client):
    """Test creating a user with invalid data."""
    response = client.post('/users', json={})
    assert response.status_code == 400


def test_update_user(client):
    """Test updating a user."""
    update_data = {"name": "Alice Updated"}
    response = client.put('/users/1', json=update_data)
    assert response.status_code == 200
    data = response.get_json()
    assert data['name'] == 'Alice Updated'
    assert data['id'] == 1


def test_update_nonexistent_user(client):
    """Test updating a user that doesn't exist."""
    response = client.put('/users/999', json={"name": "Test"})
    assert response.status_code == 404
'''

        test_file = self.work_dir / "test_app.py"
        try:
            test_file.write_text(test_code)
            self.result.add_check(
                name="create_test_suite",
                passed=True,
                output=f"Created {test_file} with 8 tests"
            )
            self.result.add_validation("test_file", str(test_file))
        except Exception as e:
            self.result.add_check(
                name="create_test_suite",
                passed=False,
                error=str(e)
            )

    def run_tests(self):
        """Run pytest test suite."""
        print("Running pytest tests...")

        def run_pytest():
            cmd = f"cd {self.work_dir} && python3 -m pytest test_app.py -v --tb=short"
            success, output, error = self.run_command(cmd, timeout=60)
            return success, output, error

        (success, output, error), duration = self.measure_time(
            "test_execution_time",
            run_pytest
        )

        # Parse test results
        test_passed = False
        pass_rate = "0/0"

        if success and output:
            # Look for pytest output like "8 passed in 0.23s"
            if "passed" in output:
                test_passed = True
                # Extract pass count
                import re
                match = re.search(r'(\d+)\s+passed', output)
                if match:
                    passed_count = match.group(1)
                    pass_rate = f"{passed_count}/8"

        self.result.add_check(
            name="pytest_tests",
            passed=test_passed,
            output=f"Tests: {pass_rate}, Duration: {duration:.2f}s",
            error=error if not test_passed else None
        )

        self.result.add_validation("test_pass_rate", pass_rate)

        # Validate output contains expected patterns
        if output:
            patterns = [
                r'test_health_endpoint.*PASSED',
                r'test_get_all_users.*PASSED',
                r'test_create_user.*PASSED',
                r'\d+\s+passed'
            ]
            self.validate_output(output, patterns, "pytest_output_validation")

    def test_api_endpoints(self):
        """Start Flask server and test HTTP endpoints."""
        print("Testing API endpoints...")

        # Start Flask server in background
        server_process = None
        try:
            cmd = f"cd {self.work_dir} && python3 app.py"
            server_process = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Wait for server to start
            if self.wait_for_service("127.0.0.1", 5000, timeout=15, service_name="flask_api"):

                # Test health endpoint
                def test_health():
                    time.sleep(0.5)  # Small delay to ensure server is ready
                    return True

                test_health()
                success, status = self.check_http_endpoint(
                    "http://127.0.0.1:5000/health",
                    expected_status=200,
                    name="health_endpoint"
                )

                # Test users endpoint
                success, status = self.check_http_endpoint(
                    "http://127.0.0.1:5000/users",
                    expected_status=200,
                    name="users_endpoint"
                )

                self.result.add_validation("api_endpoints_tested", 2)
            else:
                self.result.add_check(
                    name="flask_server_start",
                    passed=False,
                    error="Server failed to start in time"
                )

        except Exception as e:
            self.result.add_check(
                name="api_endpoint_test",
                passed=False,
                error=f"Error testing endpoints: {str(e)}"
            )
        finally:
            # Stop Flask server
            if server_process:
                server_process.terminate()
                try:
                    server_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    server_process.kill()

    def cleanup(self):
        """Clean up test files."""
        try:
            if self.work_dir.exists():
                import shutil
                shutil.rmtree(self.work_dir)
        except Exception:
            pass  # Best effort cleanup


if __name__ == "__main__":
    main_template(PythonTest)

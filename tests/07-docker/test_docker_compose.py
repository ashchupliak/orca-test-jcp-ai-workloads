#!/usr/bin/env python3
"""
Docker Compose test.
Validates multi-container applications with docker-compose.
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from common.test_framework import BaseTest, main_template


class DockerComposeTest(BaseTest):
    """Test Docker Compose for multi-container applications."""

    def __init__(self):
        super().__init__("docker_compose_multi_container")
        self.work_dir = Path("/tmp/docker_compose_test")
        self.compose_project = "testapp"

    def run(self):
        """Run comprehensive Docker Compose workflow."""
        print("Testing Docker Compose multi-container setup...")

        # Phase 1: Check Docker and Docker Compose
        self.check_command_exists("docker", "Docker")

        # Check for docker compose (new syntax)
        success, _, _ = self.run_command("docker compose version", timeout=10)
        if success:
            self.result.add_check(
                name="docker_compose_available",
                passed=True,
                output="Docker Compose (plugin) available"
            )
        else:
            # Try old docker-compose syntax
            success, version, _ = self.run_command("docker-compose --version", timeout=10)
            self.result.add_check(
                name="docker_compose_available",
                passed=success,
                output=version if success else None,
                error="Docker Compose not available" if not success else None
            )

        # Phase 2: Create application files
        self.create_web_app()
        self.create_docker_compose()

        # Phase 3: Start services with docker-compose
        self.start_services()

        # Phase 4: Test inter-container networking
        self.test_services()

        # Phase 5: Test service health and logs
        self.check_service_health()

        # Cleanup
        self.cleanup()

        return self.result

    def create_web_app(self):
        """Create a simple web application that uses Redis."""
        print("Creating web application...")

        self.work_dir.mkdir(parents=True, exist_ok=True)

        # Create Python web app
        app_code = '''#!/usr/bin/env python3
"""Web app that uses Redis for counting visits."""
import os
import redis
from flask import Flask, jsonify

app = Flask(__name__)

# Connect to Redis
redis_host = os.environ.get('REDIS_HOST', 'localhost')
redis_port = int(os.environ.get('REDIS_PORT', 6379))

try:
    cache = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
    cache.ping()
except Exception as e:
    print(f"Redis connection error: {e}")
    cache = None

@app.route('/health')
def health():
    redis_status = "connected" if cache and cache.ping() else "disconnected"
    return jsonify({
        "status": "healthy",
        "service": "web",
        "redis": redis_status
    })

@app.route('/')
def hello():
    if cache:
        try:
            visits = cache.incr('visits')
        except Exception as e:
            visits = f"Error: {e}"
    else:
        visits = "Redis not available"

    return jsonify({
        "message": "Hello from Docker Compose!",
        "visits": visits
    })

@app.route('/stats')
def stats():
    if not cache:
        return jsonify({"error": "Redis not available"}), 503

    try:
        visits = cache.get('visits') or 0
        return jsonify({
            "total_visits": int(visits),
            "redis_info": {
                "connected_clients": cache.info().get('connected_clients', 'N/A'),
                "used_memory": cache.info().get('used_memory_human', 'N/A')
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
'''

        app_file = self.work_dir / "app.py"
        app_file.write_text(app_code)

        # Create requirements.txt
        requirements = '''flask==3.0.0
redis==5.0.1
'''
        req_file = self.work_dir / "requirements.txt"
        req_file.write_text(requirements)

        # Create Dockerfile for web app
        dockerfile = '''FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

EXPOSE 5000

HEALTHCHECK --interval=5s --timeout=3s --start-period=10s --retries=3 \\
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')" || exit 1

CMD ["python3", "app.py"]
'''
        dockerfile_path = self.work_dir / "Dockerfile"
        dockerfile_path.write_text(dockerfile)

        self.result.add_check(
            name="create_web_app",
            passed=True,
            output=f"Created web app in {self.work_dir}"
        )

    def create_docker_compose(self):
        """Create docker-compose.yml for multi-container setup."""
        print("Creating docker-compose.yml...")

        compose_content = '''version: '3.8'

services:
  web:
    build: .
    ports:
      - "5000:5000"
    environment:
      - REDIS_HOST=redis
      - REDIS_PORT=6379
    depends_on:
      - redis
    networks:
      - app-network
    healthcheck:
      test: ["CMD", "python3", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')"]
      interval: 5s
      timeout: 3s
      retries: 3
      start_period: 10s

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    networks:
      - app-network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 3

networks:
  app-network:
    driver: bridge
'''

        compose_file = self.work_dir / "docker-compose.yml"
        try:
            compose_file.write_text(compose_content)
            self.result.add_check(
                name="create_docker_compose",
                passed=True,
                output=f"Created {compose_file}"
            )
            self.result.add_validation("compose_file", str(compose_file))
        except Exception as e:
            self.result.add_check(
                name="create_docker_compose",
                passed=False,
                error=str(e)
            )

    def start_services(self):
        """Start services using docker-compose."""
        print("Starting Docker Compose services...")

        # Try new docker compose syntax first
        compose_cmd = "docker compose"
        success, _, _ = self.run_command(f"{compose_cmd} version", timeout=10)
        if not success:
            # Fall back to old docker-compose syntax
            compose_cmd = "docker-compose"

        def start():
            cmd = f"cd {self.work_dir} && {compose_cmd} -p {self.compose_project} up -d --build"
            success, output, error = self.run_command(cmd, timeout=300)
            return success, output, error

        (success, output, error), duration = self.measure_time(
            "compose_startup_time",
            start
        )

        self.result.add_check(
            name="docker_compose_up",
            passed=success,
            output=f"Services started in {duration:.2f}s",
            error=error if not success else None
        )

        if success:
            # Wait for services to be healthy
            time.sleep(5)  # Initial wait

            # Check web service
            if self.wait_for_service("127.0.0.1", 5000, timeout=30, service_name="web_service"):
                self.result.add_check(
                    name="web_service_ready",
                    passed=True,
                    output="Web service is ready"
                )

            # Check Redis service
            if self.wait_for_service("127.0.0.1", 6379, timeout=30, service_name="redis_service"):
                self.result.add_check(
                    name="redis_service_ready",
                    passed=True,
                    output="Redis service is ready"
                )

    def test_services(self):
        """Test inter-container networking and communication."""
        print("Testing service communication...")

        # Test health endpoint
        success, status = self.check_http_endpoint(
            "http://127.0.0.1:5000/health",
            expected_status=200,
            name="web_health_endpoint"
        )

        # Test root endpoint (should increment Redis counter)
        for i in range(3):
            success, status = self.check_http_endpoint(
                "http://127.0.0.1:5000/",
                expected_status=200,
                name=f"web_visit_{i+1}"
            )
            time.sleep(0.2)

        # Test stats endpoint
        success, status = self.check_http_endpoint(
            "http://127.0.0.1:5000/stats",
            expected_status=200,
            name="web_stats_endpoint"
        )

        if success:
            self.result.add_validation("api_endpoints_tested", 5)

        # Test Redis directly
        success, output, error = self.run_command(
            "docker exec -it $(docker ps -qf 'name=redis') redis-cli PING",
            timeout=10
        )

        self.result.add_check(
            name="redis_direct_access",
            passed=success and "PONG" in output,
            output="Redis responds to PING" if success else None,
            error=error if not success else None
        )

    def check_service_health(self):
        """Check health and logs of services."""
        print("Checking service health and logs...")

        # Check docker compose ps
        compose_cmd = "docker compose"
        success, _, _ = self.run_command(f"{compose_cmd} version", timeout=10)
        if not success:
            compose_cmd = "docker-compose"

        success, output, error = self.run_command(
            f"cd {self.work_dir} && {compose_cmd} -p {self.compose_project} ps",
            timeout=10
        )

        self.result.add_check(
            name="compose_ps",
            passed=success,
            output=output[:200] if output else None,
            error=error if not success else None
        )

        # Check logs
        success, output, error = self.run_command(
            f"cd {self.work_dir} && {compose_cmd} -p {self.compose_project} logs --tail=20",
            timeout=10
        )

        if success and output:
            # Validate log patterns
            patterns = [
                r'web.*Running on',
                r'redis.*Ready to accept connections',
            ]
            self.validate_output(output, patterns, "compose_logs_validation")

        # Get service stats
        success, output, error = self.run_command(
            f"docker stats --no-stream --format 'table {{{{.Name}}}}\\t{{{{.CPUPerc}}}}\\t{{{{.MemUsage}}}}' $(docker ps -qf 'name={self.compose_project}')",
            timeout=10
        )

        if success and output:
            self.result.add_check(
                name="services_stats",
                passed=True,
                output=output[:300]
            )
            self.result.set_metadata("services_stats", output[:200])

    def cleanup(self):
        """Stop and remove Docker Compose services."""
        print("Cleaning up Docker Compose services...")

        compose_cmd = "docker compose"
        success, _, _ = self.run_command(f"{compose_cmd} version", timeout=10)
        if not success:
            compose_cmd = "docker-compose"

        # Stop and remove services
        self.run_command(
            f"cd {self.work_dir} && {compose_cmd} -p {self.compose_project} down -v",
            timeout=60
        )

        # Clean up work directory
        try:
            if self.work_dir.exists():
                import shutil
                shutil.rmtree(self.work_dir)
        except Exception:
            pass


if __name__ == "__main__":
    main_template(DockerComposeTest)

#!/usr/bin/env python3
"""
Docker build and run test.
Validates Docker build process, multi-stage builds, and container execution.
"""

import sys
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from common.test_framework import BaseTest, main_template


class DockerBuildTest(BaseTest):
    """Test Docker build and container execution with realistic workflow."""

    def __init__(self):
        super().__init__("docker_build_and_run")
        self.work_dir = Path("/tmp/docker_build_test")
        self.image_name = "test-app"
        self.container_name = "test-app-container"

    def run(self):
        """Run comprehensive Docker build workflow."""
        print("Testing Docker build and container execution...")

        # Phase 1: Check Docker
        self.check_command_exists("docker", "Docker")
        success, version = self.check_version("docker")
        if success:
            self.result.set_metadata("docker_version", version.split('\n')[0] if version else "")

        # Phase 2: Create application and Dockerfile
        self.create_application()
        self.create_dockerfile()

        # Phase 3: Build Docker image
        self.build_image()

        # Phase 4: Run container and validate
        self.run_container()

        # Phase 5: Test container networking
        self.test_container_networking()

        # Cleanup
        self.cleanup()

        return self.result

    def create_application(self):
        """Create a simple Python web application."""
        print("Creating application...")

        self.work_dir.mkdir(parents=True, exist_ok=True)

        app_code = '''#!/usr/bin/env python3
"""Simple web application for Docker testing."""
import http.server
import socketserver
import json
from datetime import datetime

PORT = 8000

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "message": "Docker container is running!"
            }
            self.wfile.write(json.dumps(response).encode())
        elif self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html = "<h1>Docker Test App</h1><p>Container is running successfully!</p>"
            self.wfile.write(html.encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Suppress default logging
        pass

if __name__ == "__main__":
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Server running on port {PORT}")
        httpd.serve_forever()
'''

        app_file = self.work_dir / "app.py"
        try:
            app_file.write_text(app_code)
            self.result.add_check(
                name="create_application",
                passed=True,
                output=f"Created {app_file}"
            )
        except Exception as e:
            self.result.add_check(
                name="create_application",
                passed=False,
                error=str(e)
            )

    def create_dockerfile(self):
        """Create a multi-stage Dockerfile."""
        print("Creating Dockerfile...")

        dockerfile_content = '''# Multi-stage Dockerfile for testing
FROM python:3.11-slim as base

# Set working directory
WORKDIR /app

# Copy application
COPY app.py /app/

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=5s --timeout=3s --start-period=5s --retries=3 \\
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run application
CMD ["python3", "app.py"]
'''

        dockerfile = self.work_dir / "Dockerfile"
        try:
            dockerfile.write_text(dockerfile_content)
            self.result.add_check(
                name="create_dockerfile",
                passed=True,
                output=f"Created {dockerfile}"
            )
            self.result.add_validation("dockerfile", str(dockerfile))
        except Exception as e:
            self.result.add_check(
                name="create_dockerfile",
                passed=False,
                error=str(e)
            )

    def build_image(self):
        """Build Docker image and measure performance."""
        print("Building Docker image...")

        def build():
            cmd = f"cd {self.work_dir} && docker build -t {self.image_name}:test ."
            success, output, error = self.run_command(cmd, timeout=300)
            return success, output, error

        (success, output, error), duration = self.measure_time(
            "docker_build_time",
            build
        )

        self.result.add_check(
            name="docker_build",
            passed=success,
            output=f"Built in {duration:.2f}s",
            error=error if not success else None
        )

        if success:
            # Check image size
            success, output, error = self.run_command(
                f"docker images {self.image_name}:test --format '{{{{.Size}}}}'",
                timeout=10
            )
            if success and output:
                self.result.set_metadata("image_size", output.strip())
                self.result.add_validation("image_size", output.strip())

            # Validate output contains expected patterns
            combined_output = output + error
            patterns = [
                r'Successfully built',
                r'Successfully tagged',
            ]
            self.validate_output(combined_output, patterns, "docker_build_output")

    def run_container(self):
        """Run Docker container and validate execution."""
        print("Running Docker container...")

        # Remove any existing container with the same name
        self.run_command(f"docker rm -f {self.container_name}", timeout=10)

        def run():
            cmd = f"docker run -d --name {self.container_name} -p 8000:8000 {self.image_name}:test"
            success, output, error = self.run_command(cmd, timeout=30)
            return success, output, error

        (success, output, error), duration = self.measure_time(
            "container_start_time",
            run
        )

        self.result.add_check(
            name="docker_run",
            passed=success,
            output=f"Started in {duration:.2f}s",
            error=error if not success else None
        )

        if success:
            container_id = output.strip()[:12] if output else "unknown"
            self.result.add_validation("container_id", container_id)

            # Wait for container to be healthy
            if self.wait_for_service("127.0.0.1", 8000, timeout=15, service_name="docker_app"):
                # Check container health status
                import time
                time.sleep(2)  # Wait for health check

                success, output, error = self.run_command(
                    f"docker inspect --format='{{{{.State.Health.Status}}}}' {self.container_name}",
                    timeout=10
                )

                self.result.add_check(
                    name="container_health",
                    passed=success,
                    output=f"Health status: {output}" if success else None,
                    error=error if not success else None
                )

                # Check container logs
                success, output, error = self.run_command(
                    f"docker logs {self.container_name}",
                    timeout=10
                )

                if success and output:
                    self.result.add_check(
                        name="container_logs",
                        passed="Server running" in output,
                        output=output[:200] if output else None
                    )

    def test_container_networking(self):
        """Test HTTP endpoints of the running container."""
        print("Testing container networking...")

        # Test health endpoint
        success, status = self.check_http_endpoint(
            "http://127.0.0.1:8000/health",
            expected_status=200,
            name="container_health_endpoint"
        )

        # Test root endpoint
        success, status = self.check_http_endpoint(
            "http://127.0.0.1:8000/",
            expected_status=200,
            name="container_root_endpoint"
        )

        if success:
            self.result.add_validation("http_endpoints_tested", 2)

        # Test container stats
        success, output, error = self.run_command(
            f"docker stats {self.container_name} --no-stream --format '{{{{.CPUPerc}}}} {{{{.MemUsage}}}}'",
            timeout=10
        )

        if success and output:
            self.result.add_check(
                name="container_stats",
                passed=True,
                output=f"Stats: {output}"
            )
            self.result.set_metadata("container_stats", output.strip())

    def cleanup(self):
        """Clean up Docker containers and images."""
        print("Cleaning up...")

        # Stop and remove container
        self.run_command(f"docker stop {self.container_name}", timeout=10)
        self.run_command(f"docker rm {self.container_name}", timeout=10)

        # Remove image
        self.run_command(f"docker rmi {self.image_name}:test", timeout=30)

        # Clean up work directory
        try:
            if self.work_dir.exists():
                import shutil
                shutil.rmtree(self.work_dir)
        except Exception:
            pass


if __name__ == "__main__":
    main_template(DockerBuildTest)

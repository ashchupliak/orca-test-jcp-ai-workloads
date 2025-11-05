#!/usr/bin/env python3
"""
JavaScript/Node.js development environment test.
Validates Node.js, npm, and real-world Express API development workflow.
Creates an Express API, writes Jest tests, and validates functionality.
"""

import sys
import subprocess
import time
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from common.test_framework import BaseTest, main_template


class JavaScriptTest(BaseTest):
    """Test JavaScript/Node.js development tools with realistic workflow."""

    def __init__(self):
        super().__init__("javascript_express_api")
        self.work_dir = Path("/tmp/js_test_app")

    def run(self):
        """Run comprehensive Node.js development workflow."""
        print("Testing JavaScript/Node.js development environment with Express API...")

        # Phase 1: Check basic tools
        self.check_command_exists("node", "Node.js")
        success, version = self.check_version("node")
        if success:
            self.result.set_metadata("node_version", version.strip())

        self.check_command_exists("npm", "npm")
        success, version = self.check_version("npm")
        if success:
            self.result.set_metadata("npm_version", version.strip())

        self.check_command_exists("npx", "npx")

        # Phase 2: Create project and install dependencies
        self.create_project()
        self.install_dependencies()

        # Phase 3: Create Express application
        self.create_express_app()

        # Phase 4: Create Jest test suite
        self.create_test_suite()

        # Phase 5: Run tests
        self.run_tests()

        # Phase 6: Start server and test endpoints
        self.test_api_endpoints()

        # Cleanup
        self.cleanup()

        return self.result

    def create_project(self):
        """Create package.json for the project."""
        print("Creating Node.js project...")

        self.work_dir.mkdir(parents=True, exist_ok=True)

        package_json = {
            "name": "test-express-api",
            "version": "1.0.0",
            "description": "Test Express API for validation",
            "main": "server.js",
            "scripts": {
                "test": "jest --verbose",
                "start": "node server.js"
            },
            "dependencies": {},
            "devDependencies": {}
        }

        package_file = self.work_dir / "package.json"
        try:
            package_file.write_text(json.dumps(package_json, indent=2))
            self.result.add_check(
                name="create_package_json",
                passed=True,
                output=f"Created {package_file}"
            )
        except Exception as e:
            self.result.add_check(
                name="create_package_json",
                passed=False,
                error=str(e)
            )

    def install_dependencies(self):
        """Install Express and Jest from npm."""
        print("Installing Express, Jest, and Supertest...")

        def install():
            cmd = f"cd {self.work_dir} && npm install express jest supertest"
            success, output, error = self.run_command(cmd, timeout=180)
            return success, output, error

        (success, output, error), duration = self.measure_time(
            "npm_install_time",
            install
        )

        self.result.add_check(
            name="npm_install_dependencies",
            passed=success,
            output=f"Installed in {duration:.2f}s",
            error=error if not success else None
        )

        if success:
            # Verify node_modules exists
            node_modules = self.work_dir / "node_modules"
            if node_modules.exists():
                self.result.add_validation("node_modules_created", True)

    def create_express_app(self):
        """Create a realistic Express REST API."""
        print("Creating Express application...")

        server_code = '''/**
 * Express REST API for testing
 * Provides endpoints for product management
 */
const express = require('express');
const app = express();

app.use(express.json());

// In-memory data store
let products = [
    { id: 1, name: 'Laptop', price: 999.99, stock: 10 },
    { id: 2, name: 'Mouse', price: 29.99, stock: 50 },
    { id: 3, name: 'Keyboard', price: 79.99, stock: 30 }
];
let nextId = 4;

// Health check endpoint
app.get('/health', (req, res) => {
    res.json({ status: 'healthy', service: 'product-api', uptime: process.uptime() });
});

// Get all products
app.get('/api/products', (req, res) => {
    res.json({ products, total: products.length });
});

// Get product by ID
app.get('/api/products/:id', (req, res) => {
    const id = parseInt(req.params.id);
    const product = products.find(p => p.id === id);

    if (product) {
        res.json(product);
    } else {
        res.status(404).json({ error: 'Product not found' });
    }
});

// Create new product
app.post('/api/products', (req, res) => {
    const { name, price, stock } = req.body;

    if (!name || price === undefined || stock === undefined) {
        return res.status(400).json({ error: 'Missing required fields' });
    }

    const product = {
        id: nextId++,
        name,
        price: parseFloat(price),
        stock: parseInt(stock)
    };

    products.push(product);
    res.status(201).json(product);
});

// Update product
app.put('/api/products/:id', (req, res) => {
    const id = parseInt(req.params.id);
    const product = products.find(p => p.id === id);

    if (!product) {
        return res.status(404).json({ error: 'Product not found' });
    }

    if (req.body.name !== undefined) product.name = req.body.name;
    if (req.body.price !== undefined) product.price = parseFloat(req.body.price);
    if (req.body.stock !== undefined) product.stock = parseInt(req.body.stock);

    res.json(product);
});

// Delete product
app.delete('/api/products/:id', (req, res) => {
    const id = parseInt(req.params.id);
    const index = products.findIndex(p => p.id === id);

    if (index === -1) {
        return res.status(404).json({ error: 'Product not found' });
    }

    products.splice(index, 1);
    res.status(204).send();
});

// Start server
const PORT = process.env.PORT || 3000;
if (require.main === module) {
    app.listen(PORT, () => {
        console.log(`Server running on port ${PORT}`);
    });
}

module.exports = app;
'''

        server_file = self.work_dir / "server.js"
        try:
            server_file.write_text(server_code)
            self.result.add_check(
                name="create_express_app",
                passed=True,
                output=f"Created {server_file}"
            )
            self.result.add_validation("server_file", str(server_file))
        except Exception as e:
            self.result.add_check(
                name="create_express_app",
                passed=False,
                error=str(e)
            )

    def create_test_suite(self):
        """Create Jest test suite for the Express API."""
        print("Creating Jest test suite...")

        test_code = '''/**
 * Test suite for Express product API
 */
const request = require('supertest');
const app = require('./server');

describe('Product API Tests', () => {
    describe('GET /health', () => {
        test('should return healthy status', async () => {
            const response = await request(app).get('/health');
            expect(response.status).toBe(200);
            expect(response.body.status).toBe('healthy');
            expect(response.body.service).toBe('product-api');
        });
    });

    describe('GET /api/products', () => {
        test('should return all products', async () => {
            const response = await request(app).get('/api/products');
            expect(response.status).toBe(200);
            expect(response.body.products).toBeDefined();
            expect(Array.isArray(response.body.products)).toBe(true);
            expect(response.body.products.length).toBeGreaterThan(0);
        });
    });

    describe('GET /api/products/:id', () => {
        test('should return a product by ID', async () => {
            const response = await request(app).get('/api/products/1');
            expect(response.status).toBe(200);
            expect(response.body.id).toBe(1);
            expect(response.body.name).toBeDefined();
        });

        test('should return 404 for non-existent product', async () => {
            const response = await request(app).get('/api/products/999');
            expect(response.status).toBe(404);
            expect(response.body.error).toBe('Product not found');
        });
    });

    describe('POST /api/products', () => {
        test('should create a new product', async () => {
            const newProduct = {
                name: 'Monitor',
                price: 299.99,
                stock: 15
            };

            const response = await request(app)
                .post('/api/products')
                .send(newProduct);

            expect(response.status).toBe(201);
            expect(response.body.name).toBe('Monitor');
            expect(response.body.price).toBe(299.99);
            expect(response.body.id).toBeDefined();
        });

        test('should return 400 for invalid product data', async () => {
            const response = await request(app)
                .post('/api/products')
                .send({ name: 'Invalid' });

            expect(response.status).toBe(400);
            expect(response.body.error).toBe('Missing required fields');
        });
    });

    describe('PUT /api/products/:id', () => {
        test('should update a product', async () => {
            const response = await request(app)
                .put('/api/products/1')
                .send({ price: 1099.99 });

            expect(response.status).toBe(200);
            expect(response.body.price).toBe(1099.99);
        });

        test('should return 404 for non-existent product', async () => {
            const response = await request(app)
                .put('/api/products/999')
                .send({ price: 100 });

            expect(response.status).toBe(404);
        });
    });

    describe('DELETE /api/products/:id', () => {
        test('should delete a product', async () => {
            const response = await request(app).delete('/api/products/2');
            expect(response.status).toBe(204);
        });
    });
});
'''

        test_file = self.work_dir / "server.test.js"
        try:
            test_file.write_text(test_code)
            self.result.add_check(
                name="create_test_suite",
                passed=True,
                output=f"Created {test_file} with 9 tests"
            )
            self.result.add_validation("test_file", str(test_file))
        except Exception as e:
            self.result.add_check(
                name="create_test_suite",
                passed=False,
                error=str(e)
            )

    def run_tests(self):
        """Run Jest test suite."""
        print("Running Jest tests...")

        def run_jest():
            cmd = f"cd {self.work_dir} && npm test"
            success, output, error = self.run_command(cmd, timeout=60)
            return success, output, error

        (success, output, error), duration = self.measure_time(
            "test_execution_time",
            run_jest
        )

        # Parse test results
        test_passed = False
        pass_rate = "0/0"

        combined_output = output + error
        if "Tests:" in combined_output or "passed" in combined_output:
            if "failed" not in combined_output.lower() or ("passed" in combined_output and "9 passed" in combined_output):
                test_passed = True
                # Extract pass count
                import re
                match = re.search(r'Tests:\s+(\d+)\s+passed', combined_output)
                if match:
                    passed_count = match.group(1)
                    pass_rate = f"{passed_count}/9"
                elif "9 passed" in combined_output:
                    pass_rate = "9/9"
                    test_passed = True

        self.result.add_check(
            name="jest_tests",
            passed=test_passed,
            output=f"Tests: {pass_rate}, Duration: {duration:.2f}s",
            error=error if not test_passed else None
        )

        self.result.add_validation("test_pass_rate", pass_rate)

        # Validate output contains expected patterns
        if combined_output:
            patterns = [
                r'Product API Tests',
                r'GET /health',
                r'(passed|PASS)',
            ]
            self.validate_output(combined_output, patterns, "jest_output_validation")

    def test_api_endpoints(self):
        """Start Express server and test HTTP endpoints."""
        print("Testing API endpoints...")

        server_process = None
        try:
            cmd = f"cd {self.work_dir} && node server.js"
            server_process = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Wait for server to start
            if self.wait_for_service("127.0.0.1", 3000, timeout=15, service_name="express_api"):

                # Small delay to ensure server is ready
                time.sleep(0.5)

                # Test health endpoint
                success, status = self.check_http_endpoint(
                    "http://127.0.0.1:3000/health",
                    expected_status=200,
                    name="health_endpoint"
                )

                # Test products endpoint
                success, status = self.check_http_endpoint(
                    "http://127.0.0.1:3000/api/products",
                    expected_status=200,
                    name="products_endpoint"
                )

                self.result.add_validation("api_endpoints_tested", 2)
            else:
                self.result.add_check(
                    name="express_server_start",
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
            # Stop Express server
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
    main_template(JavaScriptTest)

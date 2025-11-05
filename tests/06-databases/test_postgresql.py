#!/usr/bin/env python3
"""
PostgreSQL database operations test.
Validates PostgreSQL connectivity, migrations, and queries.
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from common.test_framework import BaseTest, main_template


class PostgreSQLTest(BaseTest):
    """Test PostgreSQL database operations with realistic workflow."""

    def __init__(self):
        super().__init__("postgresql_operations")
        self.container_name = "test-postgres"
        self.db_name = "testdb"
        self.db_user = "testuser"
        self.db_password = "testpass123"
        self.db_port = 5432

    def run(self):
        """Run comprehensive PostgreSQL workflow."""
        print("Testing PostgreSQL database operations...")

        # Phase 1: Check PostgreSQL client
        self.check_command_exists("psql", "PostgreSQL client")
        success, version = self.check_version("psql")
        if success:
            self.result.set_metadata("psql_version", version.split('\n')[0])

        # Phase 2: Start PostgreSQL container
        self.start_postgres_container()

        # Phase 3: Install Python PostgreSQL driver
        self.install_psycopg2()

        # Phase 4: Create schema and tables
        self.create_schema()

        # Phase 5: Insert test data
        self.insert_data()

        # Phase 6: Run queries
        self.run_queries()

        # Phase 7: Test transactions
        self.test_transactions()

        # Cleanup
        self.cleanup()

        return self.result

    def start_postgres_container(self):
        """Start PostgreSQL container."""
        print("Starting PostgreSQL container...")

        # Remove existing container if any
        self.run_command(f"docker rm -f {self.container_name}", timeout=10)

        env_vars = {
            "POSTGRES_USER": self.db_user,
            "POSTGRES_PASSWORD": self.db_password,
            "POSTGRES_DB": self.db_name
        }

        def start():
            success, container_id = self.start_docker_service(
                image="postgres:15-alpine",
                name=self.container_name,
                ports={self.db_port: self.db_port},
                env=env_vars,
                detach=True
            )
            return success, container_id

        (success, container_id), duration = self.measure_time(
            "postgres_start_time",
            start
        )

        if success:
            # Wait for PostgreSQL to be ready
            time.sleep(3)  # Initial wait for container startup

            # Wait for PostgreSQL port
            if self.wait_for_service("127.0.0.1", self.db_port, timeout=30, service_name="postgresql"):
                # Extra wait for PostgreSQL to accept connections
                time.sleep(2)

                # Verify connection with psql
                success, output, error = self.run_command(
                    f"docker exec {self.container_name} pg_isready -U {self.db_user}",
                    timeout=10
                )

                self.result.add_check(
                    name="postgres_ready",
                    passed=success and "accepting connections" in output,
                    output=output if success else None,
                    error=error if not success else None
                )

    def install_psycopg2(self):
        """Install psycopg2 PostgreSQL driver for Python."""
        print("Installing psycopg2...")

        def install():
            cmd = "pip3 install --user psycopg2-binary"
            success, output, error = self.run_command(cmd, timeout=120)
            return success, output, error

        (success, output, error), duration = self.measure_time(
            "psycopg2_install_time",
            install
        )

        self.result.add_check(
            name="install_psycopg2",
            passed=success,
            output=f"Installed in {duration:.2f}s",
            error=error if not success else None
        )

    def create_schema(self):
        """Create database schema with tables."""
        print("Creating database schema...")

        create_sql = """
-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create posts table
CREATE TABLE IF NOT EXISTS posts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    content TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index
CREATE INDEX IF NOT EXISTS idx_posts_user_id ON posts(user_id);
"""

        def create_tables():
            # Execute SQL via psql
            cmd = f"""docker exec -i {self.container_name} psql -U {self.db_user} -d {self.db_name} << 'EOF'
{create_sql}
EOF"""
            success, output, error = self.run_command(cmd, timeout=30)
            return success, output, error

        (success, output, error), duration = self.measure_time(
            "schema_creation_time",
            create_tables
        )

        self.result.add_check(
            name="create_schema",
            passed=success,
            output=f"Schema created in {duration:.2f}s",
            error=error if not success else None
        )

        # Verify tables exist
        if success:
            success, output, error = self.run_command(
                f"docker exec {self.container_name} psql -U {self.db_user} -d {self.db_name} -c '\\dt'",
                timeout=10
            )

            if success and "users" in output and "posts" in output:
                self.result.add_validation("tables_created", ["users", "posts"])

    def insert_data(self):
        """Insert test data into tables."""
        print("Inserting test data...")

        insert_sql = """
-- Insert users
INSERT INTO users (username, email) VALUES
    ('alice', 'alice@example.com'),
    ('bob', 'bob@example.com'),
    ('charlie', 'charlie@example.com')
ON CONFLICT (username) DO NOTHING;

-- Insert posts
INSERT INTO posts (user_id, title, content) VALUES
    (1, 'First Post', 'This is Alice''s first post'),
    (1, 'Second Post', 'Another post by Alice'),
    (2, 'Bob''s Post', 'Hello from Bob'),
    (3, 'Charlie''s Update', 'Charlie here with an update')
ON CONFLICT DO NOTHING;
"""

        def insert():
            cmd = f"""docker exec -i {self.container_name} psql -U {self.db_user} -d {self.db_name} << 'EOF'
{insert_sql}
EOF"""
            success, output, error = self.run_command(cmd, timeout=30)
            return success, output, error

        (success, output, error), duration = self.measure_time(
            "data_insert_time",
            insert
        )

        self.result.add_check(
            name="insert_data",
            passed=success,
            output=f"Data inserted in {duration:.2f}s",
            error=error if not success else None
        )

    def run_queries(self):
        """Run various SQL queries to test database operations."""
        print("Running database queries...")

        queries = [
            ("count_users", "SELECT COUNT(*) FROM users;", "3"),
            ("count_posts", "SELECT COUNT(*) FROM posts;", "4"),
            ("user_posts", "SELECT u.username, COUNT(p.id) as post_count FROM users u LEFT JOIN posts p ON u.id = p.user_id GROUP BY u.username;", "alice"),
            ("recent_posts", "SELECT title FROM posts ORDER BY created_at DESC LIMIT 2;", "Charlie"),
        ]

        all_passed = True

        for query_name, query, expected_pattern in queries:
            def run_query():
                cmd = f"docker exec {self.container_name} psql -U {self.db_user} -d {self.db_name} -t -c \"{query}\""
                success, output, error = self.run_command(cmd, timeout=10)
                return success, output, error

            (success, output, error), duration = self.measure_time(
                f"query_{query_name}_time",
                run_query
            )

            query_passed = success and expected_pattern in output

            self.result.add_check(
                name=f"query_{query_name}",
                passed=query_passed,
                output=output[:100] if output else None,
                error=error if not success else None
            )

            if not query_passed:
                all_passed = False

        if all_passed:
            self.result.add_validation("all_queries_passed", True)

    def test_transactions(self):
        """Test database transactions."""
        print("Testing transactions...")

        transaction_sql = """
BEGIN;

-- Insert a new user
INSERT INTO users (username, email) VALUES ('dave', 'dave@example.com');

-- Insert a post for the new user
INSERT INTO posts (user_id, title, content)
VALUES ((SELECT id FROM users WHERE username = 'dave'), 'Dave''s Post', 'Test post');

-- Verify the data
SELECT username FROM users WHERE username = 'dave';

COMMIT;
"""

        def run_transaction():
            cmd = f"""docker exec -i {self.container_name} psql -U {self.db_user} -d {self.db_name} << 'EOF'
{transaction_sql}
EOF"""
            success, output, error = self.run_command(cmd, timeout=30)
            return success, output, error

        (success, output, error), duration = self.measure_time(
            "transaction_time",
            run_transaction
        )

        transaction_passed = success and "dave" in output and "COMMIT" in output

        self.result.add_check(
            name="transaction_test",
            passed=transaction_passed,
            output=f"Transaction completed in {duration:.2f}s",
            error=error if not transaction_passed else None
        )

        if transaction_passed:
            self.result.add_validation("transaction_support", True)

    def cleanup(self):
        """Stop and remove PostgreSQL container."""
        print("Cleaning up PostgreSQL container...")

        self.run_command(f"docker stop {self.container_name}", timeout=10)
        self.run_command(f"docker rm {self.container_name}", timeout=10)


if __name__ == "__main__":
    main_template(PostgreSQLTest)

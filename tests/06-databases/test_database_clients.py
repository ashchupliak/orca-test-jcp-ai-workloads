#!/usr/bin/env python3
"""
Database client tools test.
Validates PostgreSQL, MySQL, and MongoDB client availability.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from common.test_framework import BaseTest, main_template


class DatabaseClientsTest(BaseTest):
    """Test database client tools."""

    def __init__(self):
        super().__init__("database_clients")

    def run(self):
        """Run database client tests."""
        print("Testing database client tools...")

        # PostgreSQL clients
        if self.check_command_exists("psql", "PostgreSQL client"):
            success, version = self.check_version("psql")
            if success:
                self.result.set_metadata("psql_version", version.split('\n')[0])

        self.check_command_exists("pg_dump", "PostgreSQL dump")
        self.check_command_exists("pg_restore", "PostgreSQL restore")

        # MySQL/MariaDB client
        if self.check_command_exists("mysql", "MySQL client"):
            success, version = self.check_version("mysql")
            if success:
                self.result.set_metadata("mysql_version", version.split('\n')[0])

        self.check_command_exists("mysqldump", "MySQL dump")

        # MongoDB client
        if self.check_command_exists("mongosh", "MongoDB shell"):
            success, version = self.check_version("mongosh")
            if success:
                self.result.set_metadata("mongosh_version", version.split('\n')[0])

        # Redis client
        if self.check_command_exists("redis-cli", "Redis CLI"):
            success, version = self.check_version("redis-cli")
            if success:
                self.result.set_metadata("redis_cli_version", version.split('\n')[0])

        return self.result


if __name__ == "__main__":
    main_template(DatabaseClientsTest)

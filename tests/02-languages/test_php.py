#!/usr/bin/env python3
"""
PHP development environment test.
Validates PHP, composer, and script execution.
"""

import sys
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from common.test_framework import BaseTest, main_template


class PHPTest(BaseTest):
    """Test PHP development tools."""

    def __init__(self):
        super().__init__("php_development")

    def run(self):
        """Run PHP toolchain tests."""
        print("="*80)
        print("PHP Development Environment Test")
        print("="*80)

        # Check php
        self.check_command_exists("php", "PHP")
        success, version = self.check_version("php")
        if success:
            self.result.set_metadata("php_version", version.split('\n')[0])

        # Check composer
        if self.check_command_exists("composer", "Composer"):
            success, version = self.check_version("composer")
            if success:
                for line in version.split('\n'):
                    if 'Composer version' in line:
                        self.result.set_metadata("composer_version", line.strip())
                        break

        # Run a simple PHP script
        self.run_php_script()

        return self.result

    def run_php_script(self):
        """Execute a simple PHP script."""
        test_code = '''<?php

function add($a, $b) {
    return $a + $b;
}

$result = add(2, 2);
echo "PHP execution works! 2 + 2 = $result\\n";

?>
'''

        test_file = Path("/tmp/hello.php")

        try:
            # Write test file
            test_file.write_text(test_code)

            # Run
            run_result = subprocess.run(
                ["php", str(test_file)],
                capture_output=True,
                text=True,
                timeout=30
            )

            expected_output = "PHP execution works!"
            success = run_result.returncode == 0 and expected_output in run_result.stdout

            self.result.add_check(
                name="php_execution",
                passed=success,
                output=run_result.stdout.strip() if success else None,
                error=run_result.stderr if not success else None
            )

        except Exception as e:
            self.result.add_check(
                name="php_execution",
                passed=False,
                error=f"Error during PHP test: {str(e)}"
            )
        finally:
            # Cleanup
            if test_file.exists():
                test_file.unlink()


if __name__ == "__main__":
    main_template(PHPTest)

#!/usr/bin/env python3
"""
Ruby development environment test.
Validates Ruby, gem, and bundler.
"""

import sys
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from common.test_framework import BaseTest, main_template


class RubyTest(BaseTest):
    """Test Ruby development tools."""

    def __init__(self):
        super().__init__("ruby_development")

    def run(self):
        """Run Ruby toolchain tests."""
        print("="*80)
        print("Ruby Development Environment Test")
        print("="*80)

        # Check ruby
        self.check_command_exists("ruby", "Ruby")
        success, version = self.check_version("ruby")
        if success:
            self.result.set_metadata("ruby_version", version.split('\n')[0])

        # Check gem
        if self.check_command_exists("gem", "RubyGems"):
            success, version = self.check_version("gem")
            if success:
                self.result.set_metadata("gem_version", version.split('\n')[0])

        # Check bundler
        self.check_command_exists("bundle", "Bundler")

        # Run a simple Ruby script
        self.run_ruby_script()

        return self.result

    def run_ruby_script(self):
        """Execute a simple Ruby script."""
        test_code = '''#!/usr/bin/env ruby

def add(a, b)
  a + b
end

result = add(2, 2)
puts "Ruby execution works! 2 + 2 = #{result}"
'''

        test_file = Path("/tmp/hello.rb")

        try:
            # Write test file
            test_file.write_text(test_code)

            # Run
            run_result = subprocess.run(
                ["ruby", str(test_file)],
                capture_output=True,
                text=True,
                timeout=30
            )

            expected_output = "Ruby execution works!"
            success = run_result.returncode == 0 and expected_output in run_result.stdout

            self.result.add_check(
                name="ruby_execution",
                passed=success,
                output=run_result.stdout.strip() if success else None,
                error=run_result.stderr if not success else None
            )

        except Exception as e:
            self.result.add_check(
                name="ruby_execution",
                passed=False,
                error=f"Error during Ruby test: {str(e)}"
            )
        finally:
            # Cleanup
            if test_file.exists():
                test_file.unlink()


if __name__ == "__main__":
    main_template(RubyTest)

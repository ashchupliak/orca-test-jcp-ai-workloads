#!/usr/bin/env python3
"""
Grazie staging environment test.
Tests Grazie API by sending a chat query asking to write a Kotlin app for 2+2.
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from common.test_framework import BaseTest, main_template

# Import Grazie client
try:
    from grazie_client import GrazieClient
    GRAZIE_CLIENT_AVAILABLE = True
except ImportError:
    GRAZIE_CLIENT_AVAILABLE = False
    GrazieClient = None


class GrazieStagingTest(BaseTest):
    """Test Grazie staging environment with chat query."""

    def __init__(self):
        super().__init__("grazie_staging")

    def run(self):
        """Run Grazie staging test."""
        print("="*80)
        print("Grazie Staging Test")
        print("="*80)
        print(f"Timestamp: {datetime.now().isoformat()}")
        print(f"Environment: staging")
        print("="*80)

        # Check if Grazie client is available
        if not GRAZIE_CLIENT_AVAILABLE:
            self.result.add_check(
                name="grazie_client_available",
                passed=False,
                error="Grazie client (grazie_client.py) not found or failed to import"
            )
            return self.result

        self.result.add_check(
            name="grazie_client_available",
            passed=True,
            output="Grazie client imported successfully"
        )

        # Check for JWT token
        jwt_token = os.getenv('GRAZIE_JWT_TOKEN') or os.getenv('USER_JWT_TOKEN')
        if not jwt_token:
            self.result.add_check(
                name="grazie_jwt_token",
                passed=False,
                error="No JWT token found. Set GRAZIE_JWT_TOKEN or USER_JWT_TOKEN environment variable"
            )
            print("\nERROR: No JWT token found!")
            print("Please set GRAZIE_JWT_TOKEN or USER_JWT_TOKEN environment variable")
            return self.result

        token_preview = jwt_token[:20] + "..." if len(jwt_token) > 20 else "***"
        print(f"Token: {token_preview}\n")

        self.result.add_check(
            name="grazie_jwt_token",
            passed=True,
            output=f"JWT token available (length: {len(jwt_token)})"
        )

        try:
            # Initialize Grazie client for staging
            print("[1] Initializing Grazie client for staging environment...")
            client = GrazieClient(environment="staging")
            print("    ✓ Client initialized successfully!\n")

            self.result.add_check(
                name="grazie_client_init",
                passed=True,
                output="Grazie client initialized for staging"
            )

            # Get available models
            print("[2] Fetching available models...")
            try:
                models = client.get_available_models()
                model_count = len(models)
                print(f"    ✓ Found {model_count} available models")
                if model_count > 0:
                    print("    First 5 models:")
                    for i, model in enumerate(models[:5], 1):
                        print(f"      {i}. {model}")
                    if model_count > 5:
                        print(f"      ... and {model_count - 5} more\n")

                self.result.add_check(
                    name="grazie_models_available",
                    passed=model_count > 0,
                    output=f"Found {model_count} models. First: {models[0] if models else 'N/A'}"
                )
                self.result.set_metadata("available_models_count", model_count)
            except Exception as e:
                print(f"    ⚠ Could not fetch models: {e}\n")
                self.result.add_check(
                    name="grazie_models_available",
                    passed=False,
                    error=f"Could not fetch models: {str(e)}"
                )

            # Prepare the query
            query = "please write a kotlin app that will do 2+2"
            system_message = "You are a helpful coding assistant."
            model = "openai-gpt-4o"

            print(f"[3] Sending query to model: {model}")
            print(f"    User message: '{query}'")
            print(f"    System message: '{system_message}'\n")

            print("[4] Waiting for response from Grazie staging...")
            print("-"*80)

            # Send the chat query
            response = client.simple_chat(
                user_message=query,
                system_message=system_message,
                profile=model
            )

            # Log the response clearly
            print("\n" + "="*80)
            print("GRAZIE RESPONSE:")
            print("="*80)
            print(response)
            print("="*80)

            # Validate response
            response_valid = response and len(response) > 0

            self.result.add_check(
                name="grazie_chat_query",
                passed=response_valid,
                output=f"Response received ({len(response)} chars)" if response_valid else None,
                error="Empty or no response received" if not response_valid else None
            )

            if response_valid:
                print(f"\n[5] ✓ Response received successfully!")
                print(f"    Response length: {len(response)} characters")
                print(f"    Response lines: {len(response.splitlines())} lines")

                self.result.set_metadata("response_length", len(response))
                self.result.set_metadata("response_lines", len(response.splitlines()))
                self.result.set_metadata("query", query)
                self.result.set_metadata("model", model)

                # Save response to file
                output_file = f"/tmp/grazie_response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                try:
                    with open(output_file, 'w') as f:
                        f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                        f.write(f"Environment: staging\n")
                        f.write(f"Query: {query}\n")
                        f.write(f"Model: {model}\n")
                        f.write("="*80 + "\n")
                        f.write("RESPONSE:\n")
                        f.write("="*80 + "\n")
                        f.write(response)
                    print(f"    Response saved to: {output_file}")

                    self.result.add_check(
                        name="response_saved",
                        passed=True,
                        output=f"Response saved to {output_file}"
                    )
                except Exception as e:
                    print(f"    ⚠ Could not save response: {e}")
                    self.result.add_check(
                        name="response_saved",
                        passed=False,
                        error=f"Could not save response: {str(e)}"
                    )
            else:
                print(f"\n[5] ✗ No response received or response was empty")

        except ValueError as e:
            print(f"\nERROR: Configuration error - {e}")
            self.result.add_check(
                name="grazie_execution",
                passed=False,
                error=f"Configuration error: {str(e)}"
            )
        except Exception as e:
            print(f"\nERROR: Unexpected error - {e}")
            import traceback
            traceback.print_exc()
            self.result.add_check(
                name="grazie_execution",
                passed=False,
                error=f"Unexpected error: {str(e)}"
            )

        print("\n" + "="*80)
        print("Grazie Staging Test Complete")
        print("="*80)

        return self.result


if __name__ == "__main__":
    main_template(GrazieStagingTest)

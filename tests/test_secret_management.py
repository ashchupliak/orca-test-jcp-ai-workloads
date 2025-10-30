#!/usr/bin/env python3
"""Secret management test - verify secrets are accessible but masked"""

import json
import sys
import os

def test_secret_management():
    """Test that secrets are properly accessible in container"""
    print("=" * 60)
    print("Secret Management Test")
    print("=" * 60)

    # Check environment variables
    secrets_to_check = [
        "OPENAI_API_KEY",
        "HUGGINGFACE_TOKEN",
        "MODEL_CACHE_DIR"
    ]

    results = {
        "status": "success",
        "secrets_found": [],
        "secrets_missing": []
    }

    print("\n🔍 Checking environment variables...")
    for secret_name in secrets_to_check:
        value = os.environ.get(secret_name)
        if value:
            # Don't print actual secret values
            masked_value = value[:4] + "..." + value[-4:] if len(value) > 8 else "***"
            print(f"   ✅ {secret_name}: {masked_value}")
            results["secrets_found"].append(secret_name)
        else:
            print(f"   ⚠️  {secret_name}: Not set")
            results["secrets_missing"].append(secret_name)

    # Verify secrets are accessible (but should be masked in API responses)
    if results["secrets_missing"]:
        results["status"] = "partial"
        print(f"\n⚠️  Some secrets are missing: {results['secrets_missing']}")
    else:
        print(f"\n✅ All expected secrets are accessible")

    print("\n📝 Note: Secrets should be MASKED in API responses")
    print("   This test verifies they are accessible in the container")

    return results

if __name__ == "__main__":
    results = test_secret_management()

    if len(sys.argv) > 1 and sys.argv[1] == "--output":
        output_file = sys.argv[2] if len(sys.argv) > 2 else "/tmp/secret-test-results.json"
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)

    sys.exit(0 if results["status"] == "success" else 1)

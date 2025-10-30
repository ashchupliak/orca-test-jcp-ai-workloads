#!/usr/bin/env python3
"""Concurrent AI request test"""

import json
import sys
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

def test_concurrent_requests(num_requests=10, api_url="http://localhost:8000"):
    """Test concurrent AI API requests"""
    print("=" * 60)
    print(f"Concurrent AI Request Test ({num_requests} requests)")
    print("=" * 60)
    
    def make_request(i):
        """Make a single API request"""
        try:
            response = requests.post(
                f"{api_url}/api/v1/infer",
                json={"prompt": f"Test request {i}"},
                timeout=30
            )
            return {
                "request_id": i,
                "status_code": response.status_code,
                "success": response.status_code == 200
            }
        except Exception as e:
            return {
                "request_id": i,
                "success": False,
                "error": str(e)
            }
    
    print(f"\n🚀 Sending {num_requests} concurrent requests...")
    start_time = time.time()
    
    results = []
    with ThreadPoolExecutor(max_workers=num_requests) as executor:
        futures = [executor.submit(make_request, i) for i in range(num_requests)]
        for future in as_completed(futures):
            results.append(future.result())
    
    total_time = time.time() - start_time
    success_count = sum(1 for r in results if r.get("success"))
    success_rate = success_count / num_requests
    
    print(f"\n📊 Results:")
    print(f"   Total requests: {num_requests}")
    print(f"   Successful: {success_count}")
    print(f"   Failed: {num_requests - success_count}")
    print(f"   Success rate: {success_rate * 100:.1f}%")
    print(f"   Total time: {total_time:.2f}s")
    print(f"   Requests/sec: {num_requests / total_time:.2f}")
    
    return {
        "status": "success" if success_rate >= 0.9 else "partial",
        "total_requests": num_requests,
        "successful_requests": success_count,
        "success_rate": success_rate,
        "total_time_seconds": round(total_time, 2),
        "requests_per_second": round(num_requests / total_time, 2)
    }

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--num-requests", type=int, default=10)
    parser.add_argument("--api-url", default="http://localhost:8000")
    parser.add_argument("--output")
    args = parser.parse_args()
    
    results = test_concurrent_requests(args.num_requests, args.api_url)
    
    if args.output:
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2)
    
    sys.exit(0 if results.get("status") == "success" else 1)


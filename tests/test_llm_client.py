#!/usr/bin/env python3
"""Test suite for LLM client functionality"""

import json
import sys
import time
from llm_client import LLMClient


def test_llm_health_check():
    """Test 1: Health check"""
    print("=" * 60)
    print("Test 1: LLM Health Check")
    print("=" * 60)
    
    try:
        client = LLMClient()
        result = client.health_check()
        
        print(f"\n✅ Status: {result.get('status')}")
        print(f"   API Base URL: {result.get('api_base_url')}")
        print(f"   API Type: {result.get('api_type')}")
        print(f"   Model Configured: {result.get('model_configured')}")
        
        if result.get("status") == "healthy":
            print("   ✅ LLM API is accessible and working")
            return {"status": "success", "test": "health_check", **result}
        else:
            print(f"   ⚠️  LLM API check failed: {result.get('error', 'Unknown error')}")
            return {"status": "failed", "test": "health_check", **result}
            
    except Exception as e:
        print(f"\n❌ Health check failed: {e}")
        return {"status": "error", "error": str(e)}


def test_simple_completion():
    """Test 2: Simple completion"""
    print("\n" + "=" * 60)
    print("Test 2: Simple Completion")
    print("=" * 60)
    
    try:
        client = LLMClient()
        prompt = "Say 'Hello' and explain what you are in one sentence."
        
        print(f"\n📝 Prompt: {prompt}")
        print("   Waiting for response...")
        
        result = client.simple_completion(
            prompt,
            max_tokens=100,
            temperature=0.7
        )
        
        if result.get("success"):
            print(f"\n✅ Completion successful!")
            print(f"   Response time: {result.get('response_time', 0):.2f}s")
            print(f"   Model: {result.get('model')}")
            print(f"   Content: {result.get('content', '')[:200]}...")
            
            usage = result.get("usage", {})
            if usage:
                print(f"   Tokens used: {usage.get('total_tokens', 'N/A')}")
            
            return {"status": "success", "test": "simple_completion", **result}
        else:
            print(f"\n❌ Completion failed: {result.get('error')}")
            return {"status": "failed", "test": "simple_completion", **result}
            
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return {"status": "error", "error": str(e)}


def test_chat_completion():
    """Test 3: Chat completion with context"""
    print("\n" + "=" * 60)
    print("Test 3: Chat Completion with Context")
    print("=" * 60)
    
    try:
        client = LLMClient()
        messages = [
            {"role": "system", "content": "You are a helpful coding assistant."},
            {"role": "user", "content": "What is Python?"}
        ]
        
        print(f"\n📝 Messages: {len(messages)} message(s)")
        print("   Waiting for response...")
        
        result = client.chat_completion(
            messages,
            max_tokens=150,
            temperature=0.7
        )
        
        if result.get("success"):
            print(f"\n✅ Chat completion successful!")
            print(f"   Response time: {result.get('response_time', 0):.2f}s")
            print(f"   Model: {result.get('model')}")
            print(f"   Content: {result.get('content', '')[:200]}...")
            
            return {"status": "success", "test": "chat_completion", **result}
        else:
            print(f"\n❌ Chat completion failed: {result.get('error')}")
            return {"status": "failed", "test": "chat_completion", **result}
            
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return {"status": "error", "error": str(e)}


def test_performance():
    """Test 4: Performance benchmark"""
    print("\n" + "=" * 60)
    print("Test 4: Performance Benchmark")
    print("=" * 60)
    
    try:
        client = LLMClient()
        prompt = "Count from 1 to 5."
        
        print(f"\n🔄 Running 5 requests...")
        results = []
        
        for i in range(5):
            print(f"   Request {i+1}/5...", end="", flush=True)
            start_time = time.time()
            result = client.simple_completion(prompt, max_tokens=50)
            elapsed = time.time() - start_time
            
            if result.get("success"):
                results.append(elapsed)
                print(f" ✅ ({elapsed:.2f}s)")
            else:
                print(f" ❌ Failed")
                break
        
        if results:
            avg_time = sum(results) / len(results)
            min_time = min(results)
            max_time = max(results)
            
            print(f"\n📊 Performance Results:")
            print(f"   Average response time: {avg_time:.2f}s")
            print(f"   Min response time: {min_time:.2f}s")
            print(f"   Max response time: {max_time:.2f}s")
            print(f"   Success rate: {len(results)}/5")
            
            return {
                "status": "success",
                "test": "performance",
                "avg_response_time": avg_time,
                "min_response_time": min_time,
                "max_response_time": max_time,
                "successful_requests": len(results)
            }
        else:
            return {"status": "failed", "test": "performance"}
            
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return {"status": "error", "error": str(e)}


def main():
    """Run all LLM tests"""
    print("=" * 60)
    print("LLM Client Test Suite")
    print("=" * 60)
    print("\nConfiguration:")
    print(f"   LLM_API_BASE_URL: {os.environ.get('LLM_API_BASE_URL', 'NOT SET')}")
    print(f"   LLM_MODEL: {os.environ.get('LLM_MODEL', 'NOT SET')}")
    print(f"   LLM_API_KEY: {'SET' if os.environ.get('LLM_API_KEY') else 'NOT SET'}")
    
    results = []
    
    # Run tests
    results.append(test_llm_health_check())
    results.append(test_simple_completion())
    results.append(test_chat_completion())
    results.append(test_performance())
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for r in results if r.get("status") == "success")
    total = len(results)
    
    for result in results:
        test_name = result.get("test", "unknown")
        status = result.get("status", "unknown")
        status_icon = "✅" if status == "success" else "❌"
        print(f"   {status_icon} {test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    # Save results
    output_file = sys.argv[1] if len(sys.argv) > 1 else "/tmp/llm-test-results.json"
    with open(output_file, "w") as f:
        json.dump({
            "summary": {
                "passed": passed,
                "total": total,
                "success_rate": passed / total if total > 0 else 0
            },
            "results": results
        }, f, indent=2)
    
    print(f"\n📄 Results saved to {output_file}")
    
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    import os
    main()


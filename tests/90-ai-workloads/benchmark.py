#!/usr/bin/env python3
"""Performance benchmark for AI workloads"""

import json
import sys
import time
import psutil
import os

def benchmark_ai_workload(duration=300):
    """Benchmark AI workload performance"""
    print("=" * 60)
    print(f"AI Workload Performance Benchmark ({duration}s)")
    print("=" * 60)

    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer

        # Load model
        print("\n📦 Loading model...")
        model_name = "gpt2"
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(model_name)

        # Benchmark metrics
        metrics = {
            "cpu_percent": [],
            "memory_mb": [],
            "inference_times": []
        }

        print(f"\n🔄 Running benchmark for {duration} seconds...")
        start_time = time.time()
        iteration = 0

        while time.time() - start_time < duration:
            iteration += 1

            # CPU and Memory
            cpu = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            metrics["cpu_percent"].append(cpu)
            metrics["memory_mb"].append(memory.used / 1024 / 1024)

            # Run inference
            prompt = f"Benchmark iteration {iteration}:"
            inputs = tokenizer(prompt, return_tensors="pt")

            inference_start = time.time()
            outputs = model.generate(**inputs, max_length=30, num_return_sequences=1)
            inference_time = time.time() - inference_start
            metrics["inference_times"].append(inference_time)

            if iteration % 10 == 0:
                elapsed = time.time() - start_time
                print(f"   Iteration {iteration}, Elapsed: {elapsed:.1f}s")

        # Calculate statistics
        results = {
            "status": "success",
            "duration_seconds": duration,
            "iterations": iteration,
            "avg_cpu_percent": sum(metrics["cpu_percent"]) / len(metrics["cpu_percent"]),
            "max_cpu_percent": max(metrics["cpu_percent"]),
            "avg_memory_mb": sum(metrics["memory_mb"]) / len(metrics["memory_mb"]),
            "max_memory_mb": max(metrics["memory_mb"]),
            "avg_inference_time": sum(metrics["inference_times"]) / len(metrics["inference_times"]),
            "min_inference_time": min(metrics["inference_times"]),
            "max_inference_time": max(metrics["inference_times"])
        }

        print(f"\n📊 Benchmark Results:")
        print(f"   Iterations: {iteration}")
        print(f"   Avg CPU: {results['avg_cpu_percent']:.1f}%")
        print(f"   Max Memory: {results['max_memory_mb']:.2f} MB")
        print(f"   Avg Inference: {results['avg_inference_time']:.3f}s")

        return results

    except ImportError:
        print("⚠️  psutil not installed, installing...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "psutil"])
        return benchmark_ai_workload(duration)
    except Exception as e:
        print(f"\n❌ Benchmark failed: {e}")
        return {
            "status": "failed",
            "error": str(e)
        }

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--duration", type=int, default=300)
    parser.add_argument("--output")
    args = parser.parse_args()

    results = benchmark_ai_workload(args.duration)

    if args.output:
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2)

    sys.exit(0 if results.get("status") == "success" else 1)



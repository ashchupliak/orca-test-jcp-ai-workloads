#!/usr/bin/env python3
"""GPU-accelerated AI inference test"""

import json
import sys
import time

def test_gpu_inference():
    """Test GPU-accelerated inference if available"""
    try:
        print("=" * 60)
        print("GPU-Accelerated AI Inference Test")
        print("=" * 60)

        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        # Check GPU availability
        cuda_available = torch.cuda.is_available()
        print(f"\n🎮 CUDA Available: {cuda_available}")

        if cuda_available:
            print(f"   GPU Device: {torch.cuda.get_device_name(0)}")
            print(f"   GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")

        model_name = "gpt2"
        print(f"\n📦 Loading model: {model_name}")

        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(model_name)

        # Move to GPU if available
        if cuda_available:
            model = model.to("cuda")
            print("   Model moved to GPU")

        # Run inference
        prompt = "Artificial intelligence will"
        inputs = tokenizer(prompt, return_tensors="pt")

        if cuda_available:
            inputs = {k: v.to("cuda") for k, v in inputs.items()}

        start_time = time.time()
        outputs = model.generate(**inputs, max_length=50, num_return_sequences=1)
        inference_time = time.time() - start_time

        result = tokenizer.decode(outputs[0], skip_special_tokens=True)

        print(f"\n✅ GPU inference successful!")
        print(f"   Prompt: {prompt}")
        print(f"   Generated: {result[:100]}...")
        print(f"   Inference time: {inference_time:.2f}s")
        print(f"   Device: {'GPU' if cuda_available else 'CPU'}")

        return {
            "status": "success",
            "gpu_available": cuda_available,
            "inference_time_seconds": round(inference_time, 2),
            "device": "gpu" if cuda_available else "cpu"
        }

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return {
            "status": "failed",
            "error": str(e)
        }

if __name__ == "__main__":
    results = test_gpu_inference()

    if len(sys.argv) > 1 and sys.argv[1] == "--output":
        output_file = sys.argv[2] if len(sys.argv) > 2 else "/tmp/gpu-results.json"
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)

    sys.exit(0 if results.get("status") == "success" else 1)



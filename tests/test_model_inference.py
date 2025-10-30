#!/usr/bin/env python3
"""Basic AI model inference test for Orca devcontainer environments"""

import json
import sys
import time
from pathlib import Path

def test_model_inference():
    """Test basic AI model inference using HuggingFace transformers"""
    try:
        print("=" * 60)
        print("AI Model Inference Test")
        print("=" * 60)
        
        # Try to import transformers
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError:
            print("❌ transformers library not installed")
            print("Installing transformers...")
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", "transformers", "torch"])
            from transformers import AutoModelForCausalLM, AutoTokenizer
        
        # Use lightweight model for testing
        model_name = "gpt2"  # Small, fast model for testing
        print(f"\n📦 Loading model: {model_name}")
        print("   (This may take a minute on first run)")
        
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(model_name)
        
        # Test inference
        print("\n🧪 Running inference test...")
        prompt = "The future of AI is"
        inputs = tokenizer(prompt, return_tensors="pt")
        
        start_time = time.time()
        outputs = model.generate(**inputs, max_length=50, num_return_sequences=1)
        inference_time = time.time() - start_time
        
        result = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Validate results
        assert len(result) > len(prompt), "Model should generate text"
        assert inference_time < 30.0, f"Inference too slow: {inference_time}s"
        
        print(f"\n✅ Inference successful!")
        print(f"   Prompt: {prompt}")
        print(f"   Generated: {result[:100]}...")
        print(f"   Inference time: {inference_time:.2f}s")
        
        # Prepare results
        test_results = {
            "status": "success",
            "test_type": "basic_inference",
            "model": model_name,
            "prompt": prompt,
            "result": result,
            "inference_time_seconds": round(inference_time, 2),
            "result_length": len(result)
        }
        
        return test_results
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return {
            "status": "failed",
            "error": str(e)
        }

def main():
    """Main test execution"""
    results = test_model_inference()
    
    # Save results if output file specified
    if len(sys.argv) > 1 and sys.argv[1] == "--output":
        output_file = sys.argv[2] if len(sys.argv) > 2 else "/tmp/inference-results.json"
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\n📄 Results saved to {output_file}")
    
    # Exit with appropriate code
    sys.exit(0 if results.get("status") == "success" else 1)

if __name__ == "__main__":
    main()


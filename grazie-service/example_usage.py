#!/usr/bin/env python3
"""
Example usage of the enhanced Grazie client with LLM parameters support.
"""

from grazie_client import GrazieClient

def main():
    # Initialize client
    client = GrazieClient(environment="staging")
    
    print("Available models:")
    for model in client.get_available_models()[:5]:  # Show first 5
        print(f"  - {model}")
    
    print("\n" + "="*50)
    
    # Example 1: Simple chat with temperature parameter
    print("Example 1: Creative response with high temperature")
    creative_params = client.create_creative_params("high")
    response = client.simple_chat(
        "Write a creative tagline for a space travel company",
        parameters=creative_params,
        prompt="creative-tagline-example"
    )
    print(f"Response: {response}")
    
    print("\n" + "="*50)
    
    # Example 2: Deterministic response
    print("Example 2: Deterministic response with seed")
    deterministic_params = client.create_deterministic_params(seed=12345)
    response = client.simple_chat(
        "Explain quantum computing in one sentence",
        parameters=deterministic_params,
        prompt="quantum-explanation"
    )
    print(f"Response: {response}")
    
    print("\n" + "="*50)
    
    # Example 3: JSON response format
    print("Example 3: Structured JSON response")
    json_params = client.create_json_response_params()
    response = client.simple_chat(
        "Return the latitude and longitude of Paris in JSON format",
        parameters=json_params,
        prompt="paris-coordinates"
    )
    print(f"Response: {response}")
    
    print("\n" + "="*50)
    
    # Example 4: Custom parameters
    print("Example 4: Custom parameters with length limit")
    custom_params = {
        'temperature': 0.7,
        'length': 50,  # Limit response to 50 tokens
        'top_p': 0.9
    }
    response = client.simple_chat(
        "Explain artificial intelligence",
        parameters=custom_params,
        prompt="ai-explanation-short"
    )
    print(f"Response: {response}")
    
    print("\n" + "="*50)
    
    # Example 5: Chat with metadata
    print("Example 5: Chat with response metadata")
    messages = [
        {"type": "system_message", "content": "You are a helpful assistant."},
        {"type": "user_message", "content": "What's the weather like?"}
    ]
    
    content, metadata = client.chat_stream_with_metadata(
        messages, 
        parameters={'temperature': 0.8},
        prompt="weather-query"
    )
    
    print(f"Content: {content}")
    print(f"Metadata: {metadata}")
    
    print("\n" + "="*50)
    
    # Example 6: Streaming with parameters
    print("Example 6: Streaming response with custom parameters")
    stream_params = {
        'temperature': 1.2,
        'top_k': 50,
        'stop_token': '.'  # Stop at first period
    }
    
    messages = [
        {"type": "user_message", "content": "Tell me about machine learning"}
    ]
    
    print("Streaming response:")
    for chunk in client.chat_stream(messages, parameters=stream_params, prompt="ml-explanation"):
        if chunk.get("type") == "Content":
            print(chunk.get("content", ""), end="", flush=True)
        elif chunk.get("type") == "FinishMetadata":
            print(f"\n[Finished: {chunk.get('reason')}]")
        elif chunk.get("type") == "QuotaMetadata":
            spent = chunk.get('spent', {}).get('amount', 'N/A')
            print(f"[Tokens spent: {spent}]")

if __name__ == "__main__":
    main() 
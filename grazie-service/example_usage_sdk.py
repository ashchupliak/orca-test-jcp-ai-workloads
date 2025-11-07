#!/usr/bin/env python3
"""
Example usage demonstrating both the original HTTP-based Grazie client 
and the new SDK-based client with Sonnet 4 support.
"""

import os
from grazie_client import GrazieClient
from grazie_sdk_client import GrazieSDKClient


def demo_original_client():
    """Demonstrate the original HTTP-based client."""
    print("=== Original HTTP Client Demo ===")
    
    # Initialize the original client
    client = GrazieClient(environment="staging")
    
    # Show available models
    print("Available models:")
    for model in client.get_available_models():
        print(f"  - {model}")
    
    # Simple chat example
    print("\n--- Simple Chat Example ---")
    response = client.simple_chat(
        user_message="Hello, how are you?",
        system_message="You are a helpful assistant.",
        profile="openai-gpt-4o"
    )
    print(f"Response: {response}")
    
    # Streaming chat example
    print("\n--- Streaming Chat Example ---")
    messages = [
        {"type": "system", "content": "You are a helpful assistant."},
        {"type": "user", "content": "Tell me a short joke."}
    ]
    
    print("Streaming response:")
    for chunk in client.chat_stream(messages, profile="openai-gpt-4o"):
        if chunk.get("type") == "Content":
            print(chunk.get("content", ""), end="", flush=True)
    print()  # New line after streaming
    
    # With parameters
    print("\n--- Chat with Parameters ---")
    creative_params = client.create_creative_params("high")
    response = client.simple_chat(
        user_message="Write a creative haiku about programming.",
        parameters=creative_params,
        profile="openai-gpt-4o"
    )
    print(f"Creative response: {response}")


def demo_sdk_client():
    """Demonstrate the new SDK-based client with Sonnet 4."""
    print("\n=== SDK Client Demo ===")
    
    try:
        # Initialize the SDK client
        client = GrazieSDKClient(environment="staging")
        
        # Show available models
        print("Available models:")
        for model in client.get_available_models():
            print(f"  - {model}")
        
        # Simple chat with default Sonnet 4
        print("\n--- Simple Chat with Sonnet 4 ---")
        response = client.simple_chat(
            user_message="Hello, how are you?",
            system_message="You are a helpful assistant."
        )
        print(f"Response: {response}")
        
        # Using the specialized Sonnet 4 method
        print("\n--- Sonnet 4 Specific Method ---")
        response = client.sonnet4_chat(
            user_message="Explain quantum computing in simple terms.",
            system_message="You are a physics teacher explaining complex topics simply."
        )
        print(f"Sonnet 4 response: {response}")
        
        # Streaming with Sonnet 4
        print("\n--- Streaming with Sonnet 4 ---")
        print("Streaming response:")
        for chunk in client.sonnet4_stream(
            user_message="Tell me a short story about a robot learning to paint.",
            system_message="You are a creative storyteller."
        ):
            if chunk.get("type") == "Content":
                print(chunk.get("content", ""), end="", flush=True)
        print()  # New line after streaming
        
        # With parameters
        print("\n--- Deterministic Response ---")
        deterministic_params = client.create_deterministic_params(seed=123)
        response = client.sonnet4_chat(
            user_message="Generate a random number between 1 and 10.",
            parameters=deterministic_params
        )
        print(f"Deterministic response: {response}")
        
        # Chat with metadata
        print("\n--- Chat with Metadata ---")
        content, metadata = client.chat_stream_with_metadata(
            messages=[
                {"type": "system", "content": "You are a helpful assistant."},
                {"type": "user", "content": "What's the capital of France?"}
            ]
        )
        print(f"Response: {content}")
        print(f"Metadata: {metadata}")
        
    except Exception as e:
        print(f"SDK Client Error: {e}")
        print("Make sure you have installed the grazie_api_gateway_client package:")
        print("pip install grazie_api_gateway_client")


def compare_clients():
    """Compare responses from both clients."""
    print("\n=== Client Comparison ===")
    
    question = "What are the main benefits of using renewable energy?"
    
    try:
        # Original client
        print("Original Client (GPT-4o):")
        original_client = GrazieClient(environment="staging")
        original_response = original_client.simple_chat(
            user_message=question,
            profile="openai-gpt-4o"
        )
        print(f"Response: {original_response[:200]}...")
        
        # SDK client with Sonnet 4
        print("\nSDK Client (Sonnet 4):")
        sdk_client = GrazieSDKClient(environment="staging")
        sdk_response = sdk_client.sonnet4_chat(user_message=question)
        print(f"Response: {sdk_response[:200]}...")
        
    except Exception as e:
        print(f"Comparison failed: {e}")


def main():
    """Main demo function."""
    # Check if JWT token is set
    if not (os.getenv('GRAZIE_JWT_TOKEN') or os.getenv('USER_JWT_TOKEN')):
        print("ERROR: Please set GRAZIE_JWT_TOKEN or USER_JWT_TOKEN environment variable")
        print("Export your JWT token like this:")
        print("export GRAZIE_JWT_TOKEN='your-jwt-token-here'")
        return
    
    print("Grazie Clients Demo")
    print("==================")
    
    # Demo original client
    try:
        demo_original_client()
    except Exception as e:
        print(f"Original client demo failed: {e}")
    
    # Demo SDK client
    try:
        demo_sdk_client()
    except Exception as e:
        print(f"SDK client demo failed: {e}")
    
    # Compare clients
    try:
        compare_clients()
    except Exception as e:
        print(f"Client comparison failed: {e}")


if __name__ == "__main__":
    main() 
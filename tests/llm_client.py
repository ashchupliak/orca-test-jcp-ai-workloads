#!/usr/bin/env python3
"""
LLM Client for testing in Orca devcontainer environments.

Supports OpenAI-compatible API providers (OpenAI, Azure OpenAI, Anthropic, etc.)
Configure via environment variables:
- LLM_API_BASE_URL: API endpoint URL (required)
- LLM_API_KEY: Authentication token (required)
- LLM_MODEL: Model name (optional, defaults to provider's default)
"""

import json
import os
import sys
import time
from typing import Dict, List, Optional, Any
from pathlib import Path

try:
    import requests
except ImportError:
    print("Installing requests...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
    import requests


class LLMClient:
    """Generic LLM client for OpenAI-compatible APIs."""
    
    def __init__(
        self,
        api_base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = 60
    ):
        """
        Initialize LLM client.
        
        Args:
            api_base_url: Base URL for LLM API (from env LLM_API_BASE_URL if not provided)
            api_key: API key/token (from env LLM_API_KEY if not provided)
            model: Model name (from env LLM_MODEL if not provided)
            timeout: Request timeout in seconds
        """
        self.api_base_url = api_base_url or os.environ.get("LLM_API_BASE_URL")
        self.api_key = api_key or os.environ.get("LLM_API_KEY")
        self.model = model or os.environ.get("LLM_MODEL")
        self.timeout = timeout
        
        if not self.api_base_url:
            raise ValueError("LLM_API_BASE_URL environment variable is required")
        if not self.api_key:
            raise ValueError("LLM_API_KEY environment variable is required")
        
        # Ensure URL doesn't end with /
        self.api_base_url = self.api_base_url.rstrip("/")
        
        # Determine API type based on URL
        self.api_type = self._detect_api_type()
        
    def _detect_api_type(self) -> str:
        """Detect API type from URL."""
        url_lower = self.api_base_url.lower()
        if "openai" in url_lower or "azure" in url_lower:
            return "openai"
        elif "anthropic" in url_lower or "claude" in url_lower:
            return "anthropic"
        else:
            # Assume OpenAI-compatible by default
            return "openai"
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers."""
        headers = {
            "Content-Type": "application/json",
        }
        
        if self.api_type == "anthropic":
            headers["x-api-key"] = self.api_key
            headers["anthropic-version"] = "2023-06-01"
        else:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        return headers
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send chat completion request.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model name (overrides instance default)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Response dict with completion results
        """
        model = model or self.model
        if not model:
            raise ValueError("Model name is required (set LLM_MODEL env var or pass model parameter)")
        
        endpoint = f"{self.api_base_url}/v1/chat/completions"
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        # Add any additional parameters
        payload.update(kwargs)
        
        # Anthropic API uses different endpoint and format
        if self.api_type == "anthropic":
            return self._anthropic_completion(messages, model, temperature, max_tokens, **kwargs)
        
        try:
            start_time = time.time()
            response = requests.post(
                endpoint,
                headers=self._get_headers(),
                json=payload,
                timeout=self.timeout
            )
            response_time = time.time() - start_time
            
            response.raise_for_status()
            result = response.json()
            
            return {
                "success": True,
                "response_time": response_time,
                "model": model,
                "content": result.get("choices", [{}])[0].get("message", {}).get("content", ""),
                "usage": result.get("usage", {}),
                "raw_response": result
            }
            
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, "status_code", None)
            }
    
    def _anthropic_completion(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: Optional[int],
        **kwargs
    ) -> Dict[str, Any]:
        """Handle Anthropic API format."""
        endpoint = f"{self.api_base_url}/v1/messages"
        
        # Convert messages format for Anthropic
        # Anthropic expects system message separately
        system_message = None
        conversation_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                conversation_messages.append(msg)
        
        payload = {
            "model": model,
            "messages": conversation_messages,
            "temperature": temperature,
        }
        
        if system_message:
            payload["system"] = system_message
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        payload.update(kwargs)
        
        try:
            start_time = time.time()
            response = requests.post(
                endpoint,
                headers=self._get_headers(),
                json=payload,
                timeout=self.timeout
            )
            response_time = time.time() - start_time
            
            response.raise_for_status()
            result = response.json()
            
            return {
                "success": True,
                "response_time": response_time,
                "model": model,
                "content": result.get("content", [{}])[0].get("text", ""),
                "usage": result.get("usage", {}),
                "raw_response": result
            }
            
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, "status_code", None)
            }
    
    def simple_completion(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Simple completion with a single user prompt.
        
        Args:
            prompt: User prompt text
            **kwargs: Additional parameters for chat_completion
            
        Returns:
            Response dict with completion results
        """
        messages = [{"role": "user", "content": prompt}]
        return self.chat_completion(messages, **kwargs)
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check if LLM API is accessible and working.
        
        Returns:
            Health check results
        """
        try:
            # Try a simple request
            result = self.simple_completion(
                "Say 'OK' if you can read this.",
                max_tokens=10,
                temperature=0.0
            )
            
            return {
                "status": "healthy" if result.get("success") else "unhealthy",
                "api_base_url": self.api_base_url,
                "api_type": self.api_type,
                "model_configured": self.model is not None,
                "response": result
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "api_base_url": self.api_base_url
            }


def main():
    """CLI interface for testing LLM client."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test LLM client")
    parser.add_argument("--test", choices=["health", "simple", "chat"], default="health")
    parser.add_argument("--prompt", default="Hello, how are you?")
    parser.add_argument("--output", help="Output file for results")
    parser.add_argument("--model", help="Override model name")
    
    args = parser.parse_args()
    
    try:
        client = LLMClient(model=args.model)
        
        if args.test == "health":
            result = client.health_check()
        elif args.test == "simple":
            result = client.simple_completion(args.prompt)
        elif args.test == "chat":
            messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": args.prompt}
            ]
            result = client.chat_completion(messages, model=args.model)
        
        if args.output:
            with open(args.output, "w") as f:
                json.dump(result, f, indent=2)
            print(f"Results saved to {args.output}")
        else:
            print(json.dumps(result, indent=2))
        
        sys.exit(0 if result.get("success") or result.get("status") == "healthy" else 1)
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()


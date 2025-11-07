#!/usr/bin/env python3

import os
import sys
import json
from grazie_client import GrazieClient

def main():
    # Get JWT token from environment variable or command line
    jwt_token = os.getenv('GRAZIE_JWT_TOKEN') or os.getenv('USER_JWT_TOKEN')
    
    # If not in environment, check command line args
    if not jwt_token and len(sys.argv) > 1:
        jwt_token = sys.argv[1]
    
    # No hardcoded fallback - token must be provided
    if not jwt_token:
        error_response = {
            "error": "JWT token required. Provide via GRAZIE_JWT_TOKEN environment variable or command line argument.",
            "models": []
        }
        print(json.dumps(error_response), file=sys.stderr)
        sys.exit(1)
    
    try:
        # Initialize client with staging environment  
        client = GrazieClient(jwt_token=jwt_token, environment="staging")
        
        # Get available models
        models = client.get_available_models()
        
        # Format for CodeCanvas integration
        models_list = []
        for model in models:
            try:
                capabilities = client.get_model_capabilities(model)
                models_list.append({
                    "name": model,
                    "id": model,
                    "provider": capabilities.get("provider", "Grazie"),
                    "features": capabilities.get("features", ["chat"]),
                    "context_limit": capabilities.get("context_limit", 0),
                    "contextLimit": capabilities.get("context_limit", 0),
                    "max_output_tokens": capabilities.get("max_output_tokens", 0),
                    "maxOutputTokens": capabilities.get("max_output_tokens", 0),
                    "display_name": model.replace("-", " ").title()
                })
            except:
                # If capabilities fail, still include basic model info
                models_list.append({
                    "name": model,
                    "id": model,
                    "provider": "Grazie",
                    "features": ["chat"],
                    "context_limit": 0,
                    "contextLimit": 0,
                    "max_output_tokens": 0,
                    "maxOutputTokens": 0,
                    "display_name": model.replace("-", " ").title()
                })
        
        # Output JSON for CodeCanvas to parse
        print(json.dumps(models_list, indent=2))
        
    except Exception as e:
        # Output error in JSON format that CodeCanvas can handle
        error_response = {
            "error": str(e),
            "models": []
        }
        print(json.dumps(error_response), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main() 
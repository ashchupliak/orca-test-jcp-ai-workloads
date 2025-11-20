#!/usr/bin/env python3
"""
Universal AI Chat Service for Orca AI Workload Containers
Provides web-based AI chat through JetBrains AI Platform (Grazie)
"""

from flask import Flask, request, jsonify
from datetime import datetime
import uuid
import os
import platform
import requests

app = Flask(__name__)

# Store conversation history (in-memory for simplicity)
conversations = {}

# JetBrains AI Platform endpoints
GRAZIE_ENDPOINTS = {
    'PREPROD': 'https://api-preprod.jetbrains.ai/user/v5/llm',
    'PRODUCTION': 'https://api.jetbrains.ai/user/v5/llm',
    'STAGING': 'https://api.stgn.jetbrains.ai/user/v5/llm'
}

@app.route('/chat', methods=['POST'])
def chat():
    """Simple chat endpoint that echoes messages back"""
    try:
        data = request.get_json()
        message = data.get('message', '')
        session_id = data.get('session_id', str(uuid.uuid4()))

        # Store in conversation history
        if session_id not in conversations:
            conversations[session_id] = []

        conversations[session_id].append({
            'role': 'user',
            'message': message,
            'timestamp': datetime.utcnow().isoformat()
        })

        # Generate simple response
        response_text = f"Hello! You said: {message}"

        conversations[session_id].append({
            'role': 'assistant',
            'message': response_text,
            'timestamp': datetime.utcnow().isoformat()
        })

        return jsonify({
            'response': response_text,
            'session_id': session_id,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'metadata': {
                'message_length': len(message),
                'service': os.environ.get('CONTAINER_NAME', 'unknown')
            }
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'container': os.environ.get('CONTAINER_NAME', 'unknown'),
        'hostname': platform.node(),
        'python_version': platform.python_version(),
        'ai_enabled': True
    })


@app.route('/api/chat', methods=['POST'])
def api_chat():
    """
    AI chat endpoint with JetBrains AI Platform integration

    Request body:
    {
        "token": "your-grazie-jwt-token",
        "environment": "PREPROD|PRODUCTION|STAGING",
        "model": "anthropic/claude-3-5-sonnet|openai/gpt-4",
        "message": "your message",
        "stream": false
    }
    """
    try:
        data = request.get_json()
        token = data.get('token', '')
        environment = data.get('environment', 'PREPROD')
        model = data.get('model', 'anthropic/claude-3-5-sonnet')
        message = data.get('message', '')
        stream = data.get('stream', False)

        if not token:
            return jsonify({'error': 'Token is required'}), 400

        if not message:
            return jsonify({'error': 'Message is required'}), 400

        # Get the base URL for the environment
        base_url = GRAZIE_ENDPOINTS.get(environment, GRAZIE_ENDPOINTS['PREPROD'])

        # Determine API path based on model
        if model.startswith('anthropic/'):
            api_path = '/anthropic/v1/messages'
            # Prepare Anthropic-style request
            grazie_request = {
                'model': model.replace('anthropic/', ''),
                'messages': [{'role': 'user', 'content': message}],
                'max_tokens': 4096,
                'stream': stream
            }
        elif model.startswith('openai/'):
            api_path = '/openai/v1/chat/completions'
            # Prepare OpenAI-style request
            grazie_request = {
                'model': model.replace('openai/', ''),
                'messages': [{'role': 'user', 'content': message}],
                'stream': stream
            }
        else:
            # Default to Anthropic
            api_path = '/anthropic/v1/messages'
            grazie_request = {
                'model': 'claude-3-5-sonnet-20241022',
                'messages': [{'role': 'user', 'content': message}],
                'max_tokens': 4096,
                'stream': stream
            }

        # Make request to JetBrains AI Platform
        full_url = f"{base_url}{api_path}"
        headers = {
            'Content-Type': 'application/json',
            'Grazie-Authenticate-JWT': token
        }

        print(f"[AI Chat] Calling {full_url} with model {model}")

        response = requests.post(
            full_url,
            json=grazie_request,
            headers=headers,
            timeout=60
        )

        if not response.ok:
            error_text = response.text
            print(f"[AI Chat] Error: {response.status_code} - {error_text}")
            return jsonify({
                'error': f'AI Platform request failed: {response.status_code}',
                'details': error_text
            }), response.status_code

        # Parse response based on API
        ai_response = response.json()

        # Extract message content
        if 'content' in ai_response and isinstance(ai_response['content'], list):
            # Anthropic format
            response_text = ai_response['content'][0].get('text', '')
        elif 'choices' in ai_response and len(ai_response['choices']) > 0:
            # OpenAI format
            response_text = ai_response['choices'][0]['message']['content']
        else:
            response_text = str(ai_response)

        return jsonify({
            'response': response_text,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'model': model,
            'environment': environment
        })

    except requests.exceptions.Timeout:
        return jsonify({'error': 'Request timeout'}), 504
    except requests.exceptions.RequestException as e:
        print(f"[AI Chat] Request error: {str(e)}")
        return jsonify({'error': f'Network error: {str(e)}'}), 500
    except Exception as e:
        print(f"[AI Chat] Error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def api_health():
    """Alternative health endpoint"""
    return health()


@app.route('/api/models', methods=['POST'])
def api_models():
    """
    Retrieve available models from JetBrains AI Platform

    Request body:
    {
        "token": "your-grazie-jwt-token",
        "environment": "PREPROD|PRODUCTION|STAGING"
    }
    """
    try:
        data = request.get_json()
        token = data.get('token', '')
        environment = data.get('environment', 'PREPROD')

        if not token:
            return jsonify({'error': 'Token is required'}), 400

        # Get the base URL for the environment
        base_url = GRAZIE_ENDPOINTS.get(environment, GRAZIE_ENDPOINTS['PREPROD'])

        # Try to fetch models from OpenAI endpoint
        full_url = f"{base_url}/openai/v1/models"
        headers = {
            'Grazie-Authenticate-JWT': token
        }

        print(f"[Models] Fetching from {full_url}")

        response = requests.get(
            full_url,
            headers=headers,
            timeout=10
        )

        if not response.ok:
            # Return hardcoded models if API call fails
            print(f"[Models] API call failed, returning defaults")
            return jsonify({
                'models': [
                    {
                        'id': 'anthropic/claude-3-5-sonnet-20241022',
                        'name': 'Claude 3.5 Sonnet',
                        'provider': 'Anthropic'
                    },
                    {
                        'id': 'anthropic/claude-3-5-haiku-20241022',
                        'name': 'Claude 3.5 Haiku',
                        'provider': 'Anthropic'
                    },
                    {
                        'id': 'openai/gpt-4o',
                        'name': 'GPT-4o',
                        'provider': 'OpenAI'
                    },
                    {
                        'id': 'openai/gpt-4o-mini',
                        'name': 'GPT-4o Mini',
                        'provider': 'OpenAI'
                    }
                ],
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            })

        # Parse response
        models_data = response.json()

        # Format models for frontend
        models = []
        if 'data' in models_data and isinstance(models_data['data'], list):
            for model in models_data['data']:
                model_id = model.get('id', '')
                # Add provider prefix if not present
                if not model_id.startswith(('anthropic/', 'openai/')):
                    provider = 'openai'  # Default to OpenAI
                    model_id = f"{provider}/{model_id}"

                models.append({
                    'id': model_id,
                    'name': model.get('name', model_id),
                    'provider': model_id.split('/')[0].title() if '/' in model_id else 'Unknown'
                })

        return jsonify({
            'models': models,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })

    except requests.exceptions.RequestException as e:
        print(f"[Models] Network error: {str(e)}")
        # Return defaults on error
        return jsonify({
            'models': [
                {
                    'id': 'anthropic/claude-3-5-sonnet-20241022',
                    'name': 'Claude 3.5 Sonnet',
                    'provider': 'Anthropic'
                },
                {
                    'id': 'openai/gpt-4o',
                    'name': 'GPT-4o',
                    'provider': 'OpenAI'
                }
            ],
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'note': 'Using default models due to API error'
        })
    except Exception as e:
        print(f"[Models] Error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/validate_token', methods=['POST'])
def validate_token():
    """
    Validate JetBrains AI Platform token

    Request body:
    {
        "token": "your-grazie-jwt-token",
        "environment": "PREPROD|PRODUCTION|STAGING"
    }
    """
    try:
        data = request.get_json()
        token = data.get('token', '')
        environment = data.get('environment', 'PREPROD')

        if not token:
            return jsonify({'valid': False, 'error': 'No token provided'}), 400

        # Get the base URL for the environment
        base_url = GRAZIE_ENDPOINTS.get(environment, GRAZIE_ENDPOINTS['PREPROD'])

        # Try to fetch models to validate token
        full_url = f"{base_url}/openai/v1/models"
        headers = {
            'Grazie-Authenticate-JWT': token
        }

        print(f"[Validate] Testing token against {full_url}")

        response = requests.get(
            full_url,
            headers=headers,
            timeout=10
        )

        if response.ok:
            return jsonify({
                'valid': True,
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'environment': environment
            })
        else:
            error_text = response.text
            print(f"[Validate] Token invalid: {response.status_code} - {error_text}")
            return jsonify({
                'valid': False,
                'error': f'Token validation failed: {response.status_code}',
                'details': error_text
            }), 401

    except requests.exceptions.RequestException as e:
        print(f"[Validate] Network error: {str(e)}")
        return jsonify({'valid': False, 'error': f'Network error: {str(e)}'}), 500
    except Exception as e:
        print(f"[Validate] Error: {str(e)}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('CHAT_PORT', 8000))
    print(f"Starting AI Chat Service on port {port}...")
    print(f"Container: {os.environ.get('CONTAINER_NAME', 'unknown')}")
    print(f"Supported environments: PREPROD, PRODUCTION, STAGING")
    print(f"Supported providers: Anthropic Claude, OpenAI")
    app.run(host='0.0.0.0', port=port, debug=False)

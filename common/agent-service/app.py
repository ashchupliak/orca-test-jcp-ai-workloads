#!/usr/bin/env python3
"""
Universal AI Agent Service for Orca AI Workload Containers
Provides agent-based AI interactions through JetBrains AI Platform (Grazie)
"""

from flask import Flask, request, jsonify
from datetime import datetime
import uuid
import os
import platform
import requests

app = Flask(__name__)

# Store agent sessions (in-memory for simplicity)
agent_sessions = {}

# JetBrains AI Platform endpoints
GRAZIE_ENDPOINTS = {
    'PREPROD': 'https://api-preprod.jetbrains.ai/user/v5/llm',
    'PRODUCTION': 'https://api.jetbrains.ai/user/v5/llm',
    'STAGING': 'https://api.stgn.jetbrains.ai/user/v5/llm'
}


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'container': os.environ.get('CONTAINER_NAME', 'unknown'),
        'hostname': platform.node(),
        'python_version': platform.python_version(),
        'service': 'agent',
        'ai_enabled': True
    })


@app.route('/api/health', methods=['GET'])
def api_health():
    """Alternative health endpoint"""
    return health()


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

        print(f"[Agent Validate] Testing token against {full_url}")

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
            print(f"[Agent Validate] Token invalid: {response.status_code} - {error_text}")
            return jsonify({
                'valid': False,
                'error': f'Token validation failed: {response.status_code}',
                'details': error_text
            }), 401

    except requests.exceptions.RequestException as e:
        print(f"[Agent Validate] Network error: {str(e)}")
        return jsonify({'valid': False, 'error': f'Network error: {str(e)}'}), 500
    except Exception as e:
        print(f"[Agent Validate] Error: {str(e)}")
        return jsonify({'error': str(e)}), 500


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

        print(f"[Agent Models] Fetching from {full_url}")

        response = requests.get(
            full_url,
            headers=headers,
            timeout=10
        )

        if not response.ok:
            # Return hardcoded models if API call fails
            print(f"[Agent Models] API call failed, returning defaults")
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
        print(f"[Agent Models] Network error: {str(e)}")
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
        print(f"[Agent Models] Error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/agent/start', methods=['POST'])
def start_agent():
    """
    Start an agent session

    Request body:
    {
        "token": "your-grazie-jwt-token",
        "environment": "PREPROD|PRODUCTION|STAGING",
        "model": "anthropic/claude-3-5-sonnet|openai/gpt-4",
        "task": "task description"
    }
    """
    try:
        data = request.get_json()
        token = data.get('token', '')
        environment = data.get('environment', 'PREPROD')
        model = data.get('model', 'anthropic/claude-3-5-sonnet')
        task = data.get('task', '')

        if not token:
            return jsonify({'error': 'Token is required'}), 400

        if not task:
            return jsonify({'error': 'Task is required'}), 400

        # Create agent session
        session_id = str(uuid.uuid4())
        agent_sessions[session_id] = {
            'task': task,
            'model': model,
            'environment': environment,
            'status': 'running',
            'created_at': datetime.utcnow().isoformat(),
            'messages': []
        }

        return jsonify({
            'session_id': session_id,
            'status': 'running',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })

    except Exception as e:
        print(f"[Agent Start] Error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/agent/status/<session_id>', methods=['GET'])
def agent_status(session_id):
    """Get agent session status"""
    if session_id not in agent_sessions:
        return jsonify({'error': 'Session not found'}), 404

    session = agent_sessions[session_id]
    return jsonify({
        'session_id': session_id,
        'status': session['status'],
        'task': session['task'],
        'created_at': session['created_at'],
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    })


@app.route('/api/agent/stop/<session_id>', methods=['POST'])
def stop_agent(session_id):
    """Stop an agent session"""
    if session_id not in agent_sessions:
        return jsonify({'error': 'Session not found'}), 404

    agent_sessions[session_id]['status'] = 'stopped'
    return jsonify({
        'session_id': session_id,
        'status': 'stopped',
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    })


if __name__ == '__main__':
    port = int(os.environ.get('AGENT_PORT', 8001))
    print(f"Starting AI Agent Service on port {port}...")
    print(f"Container: {os.environ.get('CONTAINER_NAME', 'unknown')}")
    print(f"Supported environments: PREPROD, PRODUCTION, STAGING")
    print(f"Supported providers: Anthropic Claude, OpenAI")
    app.run(host='0.0.0.0', port=port, debug=False)

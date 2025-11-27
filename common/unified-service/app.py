#!/usr/bin/env python3
"""
Unified Service - Chat, Agent, and IDE in one reliable service
Runs on ports 8000, 8001, and 8080
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import subprocess
import threading
import os
import sys

# Create three Flask apps for the three services
chat_app = Flask('chat-service')
agent_app = Flask('agent-service')

CORS(chat_app)
CORS(agent_app)

# ============================================================================
# Chat Service (Port 8000)
# ============================================================================

@chat_app.route('/health', methods=['GET'])
def chat_health():
    return jsonify({
        'status': 'healthy',
        'service': 'chat',
        'port': 8000
    }), 200

@chat_app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json() or {}
    message = data.get('message', '')
    return jsonify({
        'response': f'Chat service received: {message}',
        'service': 'chat'
    }), 200

# ============================================================================
# Agent Service (Port 8001)
# ============================================================================

@agent_app.route('/health', methods=['GET'])
def agent_health():
    return jsonify({
        'status': 'healthy',
        'service': 'agent',
        'port': 8001
    }), 200

@agent_app.route('/agent/execute', methods=['POST'])
def agent_execute():
    data = request.get_json() or {}
    command = data.get('command', '')
    return jsonify({
        'result': f'Agent executed: {command}',
        'service': 'agent'
    }), 200

# ============================================================================
# IDE Service (Port 8080) - code-server
# ============================================================================

def start_code_server():
    """Start code-server on port 8080"""
    workspace = os.environ.get('WORKSPACE_ROOT', '/workspaces/orca-test-jcp-ai-workloads')

    if not os.path.exists(workspace):
        workspace = '/workspace'

    # Check if code-server is installed
    try:
        subprocess.run(['which', 'code-server'], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        print("[IDE] code-server not installed, skipping", file=sys.stderr)
        return

    print(f"[IDE] Starting code-server on port 8080, workspace: {workspace}")

    cmd = [
        'code-server',
        '--bind-addr', '0.0.0.0:8080',
        '--auth', 'none',
        '--disable-telemetry',
        '--disable-update-check',
        '--disable-workspace-trust',
        workspace
    ]

    try:
        subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        print("[IDE] code-server started successfully")
    except Exception as e:
        print(f"[IDE] Failed to start code-server: {e}", file=sys.stderr)

# ============================================================================
# Main Entry Point
# ============================================================================

def run_chat_service():
    """Run chat service on port 8000"""
    print("[Chat] Starting on port 8000...")
    chat_app.run(host='0.0.0.0', port=8000, debug=False, use_reloader=False)

def run_agent_service():
    """Run agent service on port 8001"""
    print("[Agent] Starting on port 8001...")
    agent_app.run(host='0.0.0.0', port=8001, debug=False, use_reloader=False)

if __name__ == '__main__':
    print("=" * 60)
    print("Unified Service Starting")
    print("=" * 60)
    print("Chat Service:  http://0.0.0.0:8000/health")
    print("Agent Service: http://0.0.0.0:8001/health")
    print("IDE Service:   http://0.0.0.0:8080/healthz")
    print("=" * 60)

    # Start code-server in background
    ide_thread = threading.Thread(target=start_code_server, daemon=True)
    ide_thread.start()

    # Start agent service in background thread
    agent_thread = threading.Thread(target=run_agent_service, daemon=True)
    agent_thread.start()

    # Run chat service in main thread (this blocks)
    run_chat_service()

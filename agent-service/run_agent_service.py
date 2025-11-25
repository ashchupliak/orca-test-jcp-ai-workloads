#!/usr/bin/env python3
"""
Run the Agent Service

This script starts the Flask web application for the Agent service.
The web app provides endpoints for executing AI coding agents.

Usage:
    python run_agent_service.py

The service will be available at: http://localhost:8001
"""

import os
import sys

# Add current directory to Python path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app import app

    print("="*60)
    print("Starting Agent Service")
    print("="*60)
    print(f"Web Interface: http://localhost:8001")
    print(f"Environment: Development")
    print(f"Working Directory: {os.getcwd()}")
    print("="*60)
    print("Endpoints:")
    print("   POST /api/agent/execute - Start agent task")
    print("   GET  /api/agent/status/<id> - Get session status")
    print("   POST /api/agent/stop/<id> - Stop session")
    print("   GET  /api/agent/files/<id> - Get changed files")
    print("="*60)
    print("Press Ctrl+C to stop the server")
    print()

    app.run(debug=True, host='0.0.0.0', port=8001)

except ImportError as e:
    print(f"Import error: {e}")
    print("Please make sure all dependencies are installed:")
    print("pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"Error starting agent service: {e}")
    sys.exit(1)

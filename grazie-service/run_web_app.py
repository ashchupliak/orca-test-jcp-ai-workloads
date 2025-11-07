#!/usr/bin/env python3
"""
Run the Grazie AI Client Web App

This script starts the Flask web application for the Grazie AI client.
The web app provides a user-friendly interface to:
- Enter JWT token
- Select environment (staging/production)
- Choose from available models
- Send chat messages with advanced parameters
- View streaming responses in real-time

Usage:
    python run_web_app.py

The web app will be available at: http://localhost:8000
"""

import os
import sys

# Add current directory to Python path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app import app
    
    print("="*60)
    print("🚀 Starting Grazie AI Client Web App")
    print("="*60)
    print(f"📱 Web Interface: http://localhost:8000")
    print(f"🔧 Environment: Development")
    print(f"📁 Working Directory: {os.getcwd()}")
    print("="*60)
    print("💡 Tips:")
    print("   • Have your JWT token ready")
    print("   • Choose staging for testing, production for live use")
    print("   • Try different models and parameters")
    print("   • Enable streaming for real-time responses")
    print("="*60)
    print("Press Ctrl+C to stop the server")
    print()
    
    app.run(debug=True, host='0.0.0.0', port=8000)
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please make sure all dependencies are installed:")
    print("pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error starting web app: {e}")
    sys.exit(1) 
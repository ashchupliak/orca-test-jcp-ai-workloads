#!/usr/bin/env python3
"""
Grazie API Proxy - Translates Anthropic API calls to Grazie API
Runs locally and adds the proper Grazie-Authenticate-JWT header
"""

from flask import Flask, request, Response
import requests
import os
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Grazie API endpoints
GRAZIE_ENDPOINTS = {
    'STAGING': 'https://api-preprod.jetbrains.ai/user/v5/llm/anthropic/v1',
    'PREPROD': 'https://api-preprod.jetbrains.ai/user/v5/llm/anthropic/v1',
    'PRODUCTION': 'https://api.jetbrains.ai/user/v5/llm/anthropic/v1',
}

def get_grazie_url():
    env = os.environ.get('GRAZIE_ENVIRONMENT', 'PREPROD')
    return GRAZIE_ENDPOINTS.get(env, GRAZIE_ENDPOINTS['PREPROD'])

@app.route('/health', methods=['GET'])
def health():
    return {'status': 'healthy', 'service': 'grazie-proxy'}

@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def proxy(path):
    """Proxy all requests to Grazie API with proper authentication"""

    grazie_token = os.environ.get('GRAZIE_API_TOKEN')
    if not grazie_token:
        # Try to get from request header (x-api-key)
        grazie_token = request.headers.get('x-api-key')

    if not grazie_token:
        return {'error': 'No GRAZIE_API_TOKEN or x-api-key provided'}, 401

    # Build target URL
    target_url = f"{get_grazie_url()}/{path}"
    logger.info(f"Proxying {request.method} to: {target_url}")

    # Copy headers, replacing auth
    headers = {}
    for key, value in request.headers:
        key_lower = key.lower()
        # Skip hop-by-hop headers and auth headers we'll replace
        if key_lower in ['host', 'x-api-key', 'authorization', 'content-length']:
            continue
        headers[key] = value

    # Add Grazie authentication
    headers['Grazie-Authenticate-JWT'] = grazie_token

    # Forward the request
    try:
        resp = requests.request(
            method=request.method,
            url=target_url,
            headers=headers,
            data=request.get_data(),
            params=request.args,
            stream=True,
            timeout=300
        )

        # Stream the response back
        def generate():
            for chunk in resp.iter_content(chunk_size=1024):
                yield chunk

        # Build response headers
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        response_headers = [(name, value) for name, value in resp.raw.headers.items()
                          if name.lower() not in excluded_headers]

        return Response(generate(), status=resp.status_code, headers=response_headers)

    except requests.exceptions.RequestException as e:
        logger.error(f"Proxy error: {e}")
        return {'error': str(e)}, 502

if __name__ == '__main__':
    port = int(os.environ.get('GRAZIE_PROXY_PORT', 8090))
    print(f"Starting Grazie API Proxy on port {port}")
    print(f"Target: {get_grazie_url()}")
    print(f"Token set: {'yes' if os.environ.get('GRAZIE_API_TOKEN') else 'no'}")
    app.run(host='127.0.0.1', port=port, debug=False)

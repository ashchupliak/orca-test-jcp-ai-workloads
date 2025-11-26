#!/usr/bin/env python3
"""
Grazie API Proxy - Translates Anthropic API calls to Grazie API
Runs locally and adds the proper Grazie-Authenticate-JWT header
Uses http.server instead of Flask to avoid file descriptor issues
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import os
import sys
import urllib.request
import urllib.error
import ssl

# Grazie API endpoints
GRAZIE_ENDPOINTS = {
    'STAGING': 'https://api-preprod.jetbrains.ai/user/v5/llm/anthropic/v1',
    'PREPROD': 'https://api-preprod.jetbrains.ai/user/v5/llm/anthropic/v1',
    'PRODUCTION': 'https://api.jetbrains.ai/user/v5/llm/anthropic/v1',
}

def get_grazie_url():
    env = os.environ.get('GRAZIE_ENVIRONMENT', 'PREPROD')
    return GRAZIE_ENDPOINTS.get(env, GRAZIE_ENDPOINTS['PREPROD'])

class GrazieProxyHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        print(f"[proxy] {args[0]}", file=sys.stderr)

    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'healthy', 'service': 'grazie-proxy'}).encode())
            return
        self.proxy_request()

    def do_POST(self):
        self.proxy_request()

    def do_PUT(self):
        self.proxy_request()

    def do_DELETE(self):
        self.proxy_request()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.end_headers()

    def proxy_request(self):
        grazie_token = os.environ.get('GRAZIE_API_TOKEN')
        if not grazie_token:
            # Try to get from request header
            grazie_token = self.headers.get('x-api-key')

        if not grazie_token:
            self.send_error(401, 'No GRAZIE_API_TOKEN or x-api-key provided')
            return

        # Build target URL - re-check environment each time for dynamic switching
        grazie_url = get_grazie_url()
        target_url = f"{grazie_url}{self.path}"
        env = os.environ.get('GRAZIE_ENVIRONMENT', 'PREPROD')
        print(f"[proxy] {self.command} {self.path} -> {target_url} (env={env})", file=sys.stderr)
        sys.stderr.flush()

        # Read request body
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length) if content_length > 0 else None

        # Build headers for upstream request
        headers = {
            'Grazie-Authenticate-JWT': grazie_token,
            'Content-Type': self.headers.get('Content-Type', 'application/json'),
            'Accept': self.headers.get('Accept', 'application/json'),
        }

        # Copy anthropic headers
        for key in ['anthropic-version', 'anthropic-beta']:
            if self.headers.get(key):
                headers[key] = self.headers.get(key)

        try:
            req = urllib.request.Request(target_url, data=body, headers=headers, method=self.command)

            # Create SSL context
            ctx = ssl.create_default_context()

            with urllib.request.urlopen(req, context=ctx, timeout=300) as response:
                # Send response status
                self.send_response(response.status)

                # Copy response headers
                for key, value in response.getheaders():
                    if key.lower() not in ['transfer-encoding', 'connection']:
                        self.send_header(key, value)
                self.end_headers()

                # Stream response body
                while True:
                    chunk = response.read(4096)
                    if not chunk:
                        break
                    self.wfile.write(chunk)

        except urllib.error.HTTPError as e:
            print(f"[proxy] HTTP Error: {e.code} - {e.reason}", file=sys.stderr)
            self.send_response(e.code)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            error_body = e.read() if e.fp else b'{}'
            self.wfile.write(error_body)

        except Exception as e:
            print(f"[proxy] Error: {e}", file=sys.stderr)
            self.send_error(502, str(e))

if __name__ == '__main__':
    port = int(os.environ.get('GRAZIE_PROXY_PORT', 8090))
    print(f"Starting Grazie API Proxy on port {port}", file=sys.stderr)
    print(f"Target: {get_grazie_url()}", file=sys.stderr)
    print(f"Token set: {'yes' if os.environ.get('GRAZIE_API_TOKEN') else 'no'}", file=sys.stderr)

    server = HTTPServer(('127.0.0.1', port), GrazieProxyHandler)
    print(f"Proxy ready on http://127.0.0.1:{port}", file=sys.stderr)
    sys.stderr.flush()
    server.serve_forever()

#!/usr/bin/env python3
"""
Lightweight Agent RPC Server

This is a minimal WebSocket server that simulates what Fleet does,
but much simpler - just for testing the JCP Facade environment.

It accepts JSON-RPC 2.0 commands and executes them using Claude API.

Usage:
    export ANTHROPIC_API_KEY="sk-ant-..."
    python lightweight_agent_server.py --port 35697
"""

import asyncio
import json
import os
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any

import anthropic
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import uvicorn


class LightweightAgentServer:
    """Minimal agent server that accepts RPC commands and calls Claude"""

    def __init__(self, workspace_root: str = "/workspace"):
        self.workspace_root = Path(workspace_root)
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable required")

        self.client = anthropic.Anthropic(api_key=api_key)
        self.request_id = 0

    async def handle_agent_task(self, task: str) -> Dict[str, Any]:
        """
        Handle an agent.task RPC call

        This sends the task to Claude and returns the response
        """
        print(f"[Agent Task] {task}")

        try:
            # Build context about the workspace
            context = self._build_workspace_context()

            # Call Claude API
            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4096,
                system=f"""You are an AI coding assistant running in a development environment.

Workspace root: {self.workspace_root}
Current working directory: {os.getcwd()}

{context}

When asked to create or modify files, provide the complete file content.
When asked to execute commands, explain what the command does.""",
                messages=[{
                    "role": "user",
                    "content": task
                }]
            )

            # Extract response
            response_text = message.content[0].text

            return {
                "status": "completed",
                "output": response_text,
                "model": message.model,
                "usage": {
                    "input_tokens": message.usage.input_tokens,
                    "output_tokens": message.usage.output_tokens
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    def _build_workspace_context(self) -> str:
        """Build context about the current workspace"""
        try:
            # List files in workspace
            files = list(self.workspace_root.glob("**/*"))
            file_list = [str(f.relative_to(self.workspace_root)) for f in files if f.is_file()][:50]

            context = f"Files in workspace (first 50):\n"
            for f in file_list:
                context += f"  - {f}\n"

            return context
        except Exception as e:
            return f"Could not read workspace: {e}"

    async def handle_file_list(self, path: str) -> Dict[str, Any]:
        """List files in a directory"""
        try:
            target = self.workspace_root / path.lstrip("/")
            if not target.exists():
                return {"error": f"Path does not exist: {path}"}

            if target.is_file():
                return {"files": [{"name": target.name, "type": "file"}]}

            files = []
            for item in target.iterdir():
                files.append({
                    "name": item.name,
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else None
                })

            return {"files": files}
        except Exception as e:
            return {"error": str(e)}

    async def handle_file_read(self, path: str) -> Dict[str, Any]:
        """Read a file"""
        try:
            target = self.workspace_root / path.lstrip("/")
            if not target.exists():
                return {"error": f"File does not exist: {path}"}

            content = target.read_text()
            return {"content": content}
        except Exception as e:
            return {"error": str(e)}

    async def handle_file_write(self, path: str, content: str) -> Dict[str, Any]:
        """Write to a file"""
        try:
            target = self.workspace_root / path.lstrip("/")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)
            return {"status": "success", "path": str(path)}
        except Exception as e:
            return {"error": str(e)}

    async def handle_exec(self, command: str) -> Dict[str, Any]:
        """Execute a shell command"""
        try:
            print(f"[Exec] {command}")
            result = subprocess.run(
                command,
                shell=True,
                cwd=self.workspace_root,
                capture_output=True,
                text=True,
                timeout=30
            )

            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {"error": "Command timeout after 30 seconds"}
        except Exception as e:
            return {"error": str(e)}

    async def handle_rpc_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a JSON-RPC 2.0 request"""
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")

        # Route to appropriate handler
        if method == "agent.task":
            result = await self.handle_agent_task(params.get("task", ""))
        elif method == "file.list":
            result = await self.handle_file_list(params.get("path", "/workspace"))
        elif method == "file.read":
            result = await self.handle_file_read(params.get("path"))
        elif method == "file.write":
            result = await self.handle_file_write(params.get("path"), params.get("content", ""))
        elif method == "exec":
            result = await self.handle_exec(params.get("command"))
        else:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }

        # Build response
        if "error" in result:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32000,
                    "message": result["error"]
                }
            }
        else:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result
            }


# FastAPI application
app = FastAPI(title="Lightweight Agent RPC Server")
agent_server = None


@app.on_event("startup")
async def startup():
    global agent_server
    workspace = os.getenv("WORKSPACE_ROOT", "/workspace")
    agent_server = LightweightAgentServer(workspace)
    print(f"🚀 Agent server initialized")
    print(f"   Workspace: {workspace}")
    print(f"   Claude model: claude-3-5-sonnet-20241022")


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "running",
        "server": "Lightweight Agent RPC Server",
        "workspace": str(agent_server.workspace_root) if agent_server else None
    }


@app.websocket("/websocket")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for JSON-RPC 2.0 communication"""
    await websocket.accept()
    print(f"🔌 Client connected: {websocket.client}")

    try:
        while True:
            # Receive JSON-RPC request
            data = await websocket.receive_text()

            try:
                request = json.loads(data)
                print(f"📥 Request: {request.get('method')} (id={request.get('id')})")

                # Handle request
                response = await agent_server.handle_rpc_request(request)

                # Send response
                await websocket.send_text(json.dumps(response))
                print(f"📤 Response sent (id={response.get('id')})")

            except json.JSONDecodeError:
                # Invalid JSON
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32700,
                        "message": "Parse error: Invalid JSON"
                    }
                }
                await websocket.send_text(json.dumps(error_response))

    except WebSocketDisconnect:
        print(f"👋 Client disconnected: {websocket.client}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Lightweight Agent RPC Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=35697, help="Port to listen on")
    parser.add_argument("--workspace", default="/workspace", help="Workspace root directory")

    args = parser.parse_args()

    # Set workspace root
    os.environ["WORKSPACE_ROOT"] = args.workspace

    print("=" * 70)
    print("🚀 Starting Lightweight Agent RPC Server")
    print("=" * 70)
    print(f"   Host: {args.host}")
    print(f"   Port: {args.port}")
    print(f"   Workspace: {args.workspace}")
    print(f"   WebSocket URL: ws://{args.host}:{args.port}/websocket")
    print("=" * 70)
    print()

    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_level="info"
    )

#!/usr/bin/env python3
"""
Universal AI Agent Service for Orca AI Workload Containers
Provides agent-based AI interactions through JetBrains AI Platform (Grazie)
with Git workflow integration for Claude Code.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import uuid
import os
import platform
import requests
import subprocess
import tempfile
import shutil
import threading
import re

app = Flask(__name__)

# Enable CORS for all routes - required for orca-lab proxy access
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# Store agent sessions (in-memory for simplicity)
agent_sessions = {}

# JetBrains AI Platform endpoints
GRAZIE_ENDPOINTS = {
    'PREPROD': 'https://api-preprod.jetbrains.ai/user/v5/llm',
    'PRODUCTION': 'https://api.jetbrains.ai/user/v5/llm',
    'STAGING': 'https://api.stgn.jetbrains.ai/user/v5/llm'
}

# Anthropic API endpoints for Claude (via Grazie)
ANTHROPIC_ENDPOINTS = {
    'PREPROD': 'https://api-preprod.jetbrains.ai/user/v5/llm/anthropic/v1',
    'PRODUCTION': 'https://api.jetbrains.ai/user/v5/llm/anthropic/v1',
    'STAGING': 'https://api.stgn.jetbrains.ai/user/v5/llm/anthropic/v1'
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
                        'id': 'claude-sonnet-4-5-20250929',
                        'name': 'Claude Sonnet 4.5',
                        'provider': 'Anthropic'
                    },
                    {
                        'id': 'claude-opus-4-1-20250805',
                        'name': 'Claude Opus 4.1',
                        'provider': 'Anthropic'
                    },
                    {
                        'id': 'claude-3-5-haiku-20241022',
                        'name': 'Claude 3.5 Haiku',
                        'provider': 'Anthropic'
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
                models.append({
                    'id': model_id,
                    'name': model.get('name', model_id),
                    'provider': 'Anthropic' if 'claude' in model_id.lower() else 'OpenAI'
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
                    'id': 'claude-sonnet-4-5-20250929',
                    'name': 'Claude Sonnet 4.5',
                    'provider': 'Anthropic'
                },
                {
                    'id': 'claude-opus-4-1-20250805',
                    'name': 'Claude Opus 4.1',
                    'provider': 'Anthropic'
                }
            ],
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'note': 'Using default models due to API error'
        })
    except Exception as e:
        print(f"[Agent Models] Error: {str(e)}")
        return jsonify({'error': str(e)}), 500


def run_command(cmd, cwd=None, env=None):
    """Run a shell command and return output"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        return result.returncode == 0, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return False, "Command timed out"
    except Exception as e:
        return False, str(e)


def get_changed_files(repo_path):
    """Get list of changed files in a git repo"""
    files = []
    success, output = run_command("git diff --name-status HEAD~1 HEAD 2>/dev/null || git diff --name-status HEAD", cwd=repo_path)
    if success:
        for line in output.strip().split('\n'):
            if line:
                parts = line.split('\t')
                if len(parts) >= 2:
                    status = parts[0]
                    filepath = parts[1]
                    file_type = 'modified'
                    if status.startswith('A'):
                        file_type = 'created'
                    elif status.startswith('D'):
                        file_type = 'deleted'

                    # Try to read file content for non-deleted files
                    content = None
                    if file_type != 'deleted':
                        try:
                            full_path = os.path.join(repo_path, filepath)
                            if os.path.exists(full_path) and os.path.getsize(full_path) < 10000:
                                with open(full_path, 'r') as f:
                                    content = f.read()
                        except:
                            pass

                    files.append({
                        'path': filepath,
                        'type': file_type,
                        'content': content
                    })
    return files


def execute_git_task(session_id, token, environment, model, task, git_repo_url, git_token, branch_name):
    """Execute the full Git workflow with Claude Code"""
    session = agent_sessions.get(session_id)
    if not session:
        return

    temp_dir = None
    try:
        # Step 1: Create temp directory
        session['progress'].append('Creating temporary workspace...')
        temp_dir = tempfile.mkdtemp(prefix='claude-agent-')
        session['temp_dir'] = temp_dir

        # Step 2: Clone repository
        session['progress'].append(f'Cloning repository...')
        session['git_status']['cloning'] = True

        # Prepare clone URL with authentication
        clone_url = git_repo_url
        if git_token and 'github.com' in git_repo_url:
            # Convert SSH URL to HTTPS with token
            if git_repo_url.startswith('git@github.com:'):
                # SSH format: git@github.com:user/repo.git
                repo_path = git_repo_url.replace('git@github.com:', '').replace('.git', '')
                clone_url = f'https://{git_token}@github.com/{repo_path}.git'
            elif git_repo_url.startswith('https://github.com/'):
                # Already HTTPS, add token
                clone_url = git_repo_url.replace('https://github.com/', f'https://{git_token}@github.com/')

        repo_dir = os.path.join(temp_dir, 'repo')
        success, output = run_command(f'git clone --depth=50 "{clone_url}" repo', cwd=temp_dir)
        if not success:
            raise Exception(f'Failed to clone repository: {output}')

        session['git_status']['cloned'] = True
        session['progress'].append('Repository cloned successfully')

        # Step 3: Configure git
        session['progress'].append('Configuring git...')
        run_command('git config user.email "claude-agent@orca-lab.local"', cwd=repo_dir)
        run_command('git config user.name "Claude Agent"', cwd=repo_dir)

        # Step 4: Create branch
        session['progress'].append(f'Creating branch: {branch_name}')
        success, output = run_command(f'git checkout -b "{branch_name}"', cwd=repo_dir)
        if not success:
            raise Exception(f'Failed to create branch: {output}')
        session['git_status']['branch_created'] = True

        # Step 5: Execute Claude Code
        session['progress'].append('Executing Claude Code agent...')
        session['progress'].append(f'Task: {task}')

        # Set up environment for Claude Code
        claude_env = os.environ.copy()
        anthropic_base = ANTHROPIC_ENDPOINTS.get(environment, ANTHROPIC_ENDPOINTS['STAGING'])
        claude_env['ANTHROPIC_API_KEY'] = token
        claude_env['ANTHROPIC_BASE_URL'] = anthropic_base

        # Try to use Claude Code CLI if available
        claude_cmd = f'claude --print "{task}"'
        success, output = run_command(claude_cmd, cwd=repo_dir, env=claude_env)

        if not success:
            # Claude Code not available, use Anthropic API directly
            session['progress'].append('Claude Code CLI not available, using API directly...')

            # Call Anthropic API via Grazie
            api_response = call_anthropic_api(token, environment, model, task, repo_dir)
            if api_response:
                session['progress'].append('Received response from Claude API')
                # Apply the suggested changes (simplified)
                apply_claude_suggestions(repo_dir, api_response, session)
            else:
                session['progress'].append('Warning: Could not get response from API')
        else:
            session['progress'].append('Claude Code executed successfully')

        # Step 6: Check for changes
        session['progress'].append('Checking for changes...')
        success, status_output = run_command('git status --porcelain', cwd=repo_dir)

        if status_output.strip():
            # There are changes to commit
            session['progress'].append('Changes detected, staging files...')
            run_command('git add -A', cwd=repo_dir)

            # Step 7: Commit changes
            commit_msg = f"Claude Agent: {task[:50]}..." if len(task) > 50 else f"Claude Agent: {task}"
            success, output = run_command(f'git commit -m "{commit_msg}"', cwd=repo_dir)
            if success:
                session['git_status']['committed'] = True
                session['progress'].append('Changes committed')

                # Get changed files
                session['files'] = get_changed_files(repo_dir)

                # Step 8: Push to remote
                session['progress'].append(f'Pushing branch {branch_name} to remote...')
                success, output = run_command(f'git push -u origin "{branch_name}"', cwd=repo_dir)
                if success:
                    session['git_status']['pushed'] = True
                    session['progress'].append(f'Branch {branch_name} pushed successfully')
                else:
                    session['progress'].append(f'Warning: Push failed - {output}')
            else:
                session['progress'].append('No changes to commit')
        else:
            session['progress'].append('No changes were made by the agent')

        # Mark as completed
        session['status'] = 'completed'
        session['progress'].append('Task completed successfully!')

    except Exception as e:
        session['status'] = 'error'
        session['error'] = str(e)
        session['progress'].append(f'Error: {str(e)}')
        print(f"[Git Task] Error: {str(e)}")
    finally:
        # Cleanup temp directory (delayed to allow file reading)
        if temp_dir and os.path.exists(temp_dir):
            try:
                # Keep for a bit in case we need to read files
                threading.Timer(60.0, lambda: shutil.rmtree(temp_dir, ignore_errors=True)).start()
            except:
                pass


def call_anthropic_api(token, environment, model, task, repo_path):
    """Call Claude API via Grazie to get suggestions"""
    try:
        base_url = ANTHROPIC_ENDPOINTS.get(environment, ANTHROPIC_ENDPOINTS['STAGING'])

        # Get some context from the repository
        context_files = []
        for root, dirs, files in os.walk(repo_path):
            # Skip .git directory
            dirs[:] = [d for d in dirs if d != '.git']
            for f in files[:10]:  # Limit to first 10 files
                try:
                    filepath = os.path.join(root, f)
                    if os.path.getsize(filepath) < 5000:  # Only small files
                        with open(filepath, 'r') as file:
                            content = file.read()
                            rel_path = os.path.relpath(filepath, repo_path)
                            context_files.append(f"File: {rel_path}\n```\n{content}\n```")
                except:
                    pass

        context = "\n\n".join(context_files[:5])  # Use first 5 files as context

        prompt = f"""You are a coding assistant. Based on the following task and repository context, provide specific code changes.

Task: {task}

Repository Context:
{context}

Provide your response as specific file modifications. For each file, use this format:
FILE: path/to/file
```
new file content
```

Only include files that need to be modified or created."""

        headers = {
            'Content-Type': 'application/json',
            'Grazie-Authenticate-JWT': token,
            'anthropic-version': '2023-06-01'
        }

        response = requests.post(
            f"{base_url}/messages",
            headers=headers,
            json={
                'model': model,
                'max_tokens': 4000,
                'messages': [{'role': 'user', 'content': prompt}]
            },
            timeout=120
        )

        if response.ok:
            data = response.json()
            if 'content' in data and len(data['content']) > 0:
                return data['content'][0].get('text', '')

        return None
    except Exception as e:
        print(f"[Anthropic API] Error: {str(e)}")
        return None


def apply_claude_suggestions(repo_path, response_text, session):
    """Parse and apply Claude's suggestions to the repository"""
    try:
        # Parse FILE: blocks from the response
        file_pattern = r'FILE:\s*(.+?)\n```(?:\w+)?\n(.*?)```'
        matches = re.findall(file_pattern, response_text, re.DOTALL)

        for filepath, content in matches:
            filepath = filepath.strip()
            content = content.strip()

            full_path = os.path.join(repo_path, filepath)

            # Create directory if needed
            os.makedirs(os.path.dirname(full_path), exist_ok=True)

            # Write the file
            with open(full_path, 'w') as f:
                f.write(content)

            session['progress'].append(f'Modified: {filepath}')

        if not matches:
            session['progress'].append('No file changes detected in response')

    except Exception as e:
        session['progress'].append(f'Error applying changes: {str(e)}')


@app.route('/api/agent/git-task', methods=['POST'])
def git_task():
    """
    Execute a Git-based task with Claude Code

    Request body:
    {
        "token": "your-grazie-jwt-token",
        "environment": "PREPROD|PRODUCTION|STAGING",
        "model": "claude-sonnet-4-5-20250929",
        "task": "task description",
        "git_repo_url": "git@github.com:user/repo.git",
        "git_token": "github-token",
        "branch_name": "feature/my-branch"
    }
    """
    try:
        data = request.get_json()
        token = data.get('token', '')
        environment = data.get('environment', 'STAGING')
        model = data.get('model', 'claude-sonnet-4-5-20250929')
        task = data.get('task', '')
        git_repo_url = data.get('git_repo_url', '')
        git_token = data.get('git_token', '')
        branch_name = data.get('branch_name', '')

        # Validation
        if not token:
            return jsonify({'error': 'Grazie token is required'}), 400
        if not task:
            return jsonify({'error': 'Task description is required'}), 400
        if not git_repo_url:
            return jsonify({'error': 'Git repository URL is required'}), 400
        if not branch_name:
            branch_name = f"claude-agent/{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        # Create session
        session_id = str(uuid.uuid4())
        agent_sessions[session_id] = {
            'task': task,
            'model': model,
            'environment': environment,
            'status': 'running',
            'created_at': datetime.utcnow().isoformat(),
            'branch_name': branch_name,
            'git_repo_url': git_repo_url,
            'progress': [],
            'git_status': {
                'cloning': False,
                'cloned': False,
                'branch_created': False,
                'committed': False,
                'pushed': False
            },
            'files': [],
            'error': None
        }

        # Start background task
        thread = threading.Thread(
            target=execute_git_task,
            args=(session_id, token, environment, model, task, git_repo_url, git_token, branch_name)
        )
        thread.daemon = True
        thread.start()

        return jsonify({
            'session_id': session_id,
            'status': 'running',
            'branch_name': branch_name,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })

    except Exception as e:
        print(f"[Git Task] Error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/agent/start', methods=['POST'])
def start_agent():
    """
    Start an agent session (legacy endpoint)

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
        model = data.get('model', 'claude-sonnet-4-5-20250929')
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
            'progress': [],
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

    # Get new progress messages since last poll
    progress = session.get('progress', [])

    response_data = {
        'session_id': session_id,
        'status': session['status'],
        'task': session['task'],
        'created_at': session['created_at'],
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }

    # Include git-specific fields if present
    if 'git_status' in session:
        response_data['git_status'] = session['git_status']
    if 'branch_name' in session:
        response_data['branch_name'] = session['branch_name']
    if 'files' in session:
        response_data['files'] = session['files']
    if 'error' in session and session['error']:
        response_data['error'] = session['error']
    if progress:
        response_data['progress'] = progress

    return jsonify(response_data)


@app.route('/api/agent/files/<session_id>', methods=['GET'])
def agent_files(session_id):
    """Get files changed by the agent"""
    if session_id not in agent_sessions:
        return jsonify({'error': 'Session not found'}), 404

    session = agent_sessions[session_id]
    return jsonify({
        'session_id': session_id,
        'files': session.get('files', []),
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
    print(f"Features: Git workflow, Claude Code integration")
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)

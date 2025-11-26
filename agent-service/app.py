#!/usr/bin/env python3
"""
Agent Service - Flask web app for AI agent execution
Provides endpoints for Claude Code and Codex CLI agent execution on port 8001
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import traceback
import os
import subprocess
import uuid
import threading
import logging
from datetime import datetime
from pathlib import Path

app = Flask(__name__)

# Enable CORS for all routes to allow requests from the Orca UI
CORS(app, resources={r"/*": {"origins": "*"}})

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# In-memory session storage
sessions = {}


class AgentSession:
    """Represents an agent execution session"""

    def __init__(self, session_id: str, agent: str, task: str, config: dict):
        self.session_id = session_id
        self.agent = agent
        self.task = task
        self.config = config
        self.status = 'pending'
        self.progress = []
        self.error = None
        self.files = []
        self.output = ''
        self.created_at = datetime.utcnow()
        self.completed_at = None
        self.process = None

    def add_progress(self, message: str):
        timestamp = datetime.utcnow().isoformat()
        self.progress.append(f"[{timestamp}] {message}")
        logger.info(f"[{self.session_id}] {message}")

    def to_dict(self):
        return {
            'session_id': self.session_id,
            'agent': self.agent,
            'task': self.task,
            'status': self.status,
            'progress': self.progress,
            'error': self.error,
            'files': self.files,
            'output': self.output,
            'created_at': self.created_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }


def get_grazie_base_url(environment: str) -> str:
    """Get the Grazie API base URL for the specified environment"""
    env_upper = environment.upper()
    if env_upper == 'PRODUCTION':
        return "https://api.jetbrains.ai/user/v5/llm"
    else:
        # STAGING, PREPROD use preprod endpoint
        return "https://api-preprod.jetbrains.ai/user/v5/llm"


def run_claude_code(session: AgentSession):
    """Execute task using Claude Code agent"""
    try:
        session.status = 'running'
        session.add_progress("Initializing Claude Code agent...")

        token = session.config.get('token')
        environment = session.config.get('environment', 'PREPROD')
        model = session.config.get('model', 'claude-3-5-sonnet-20241022')
        github_token = session.config.get('github_token')
        github_repo = session.config.get('github_repo')

        base_url = get_grazie_base_url(environment)

        # Set up environment for Claude Code
        env = os.environ.copy()
        env['GRAZIE_API_TOKEN'] = token
        env['GRAZIE_ENVIRONMENT'] = environment
        env['ANTHROPIC_API_KEY'] = 'use-grazie-token'
        env['ANTHROPIC_BASE_URL'] = f"{base_url}/anthropic/v1"

        if github_token:
            env['GITHUB_TOKEN'] = github_token
            session.add_progress("GitHub token configured for commit/push operations")

        # Create workspace directory
        workspace = Path('/workspace/agent-workspace')
        workspace.mkdir(parents=True, exist_ok=True)

        # If GitHub repo provided, clone it
        if github_repo:
            session.add_progress(f"Cloning repository: {github_repo}")
            repo_name = github_repo.split('/')[-1].replace('.git', '')
            repo_path = workspace / repo_name

            if repo_path.exists():
                session.add_progress("Repository already exists, pulling latest changes...")
                subprocess.run(['git', 'pull'], cwd=repo_path, env=env, capture_output=True)
            else:
                clone_url = github_repo
                if github_token and 'github.com' in github_repo:
                    # Use token for authentication
                    clone_url = github_repo.replace('https://', f'https://{github_token}@')
                subprocess.run(['git', 'clone', clone_url], cwd=workspace, env=env, capture_output=True)

            workspace = repo_path

        session.add_progress(f"Using model: {model}")
        session.add_progress(f"Working directory: {workspace}")
        session.add_progress(f"Executing task: {session.task}")

        # Check if claude-code is available
        claude_check = subprocess.run(['which', 'claude-code'], capture_output=True, text=True)

        if claude_check.returncode != 0:
            # Try alternative command names
            for cmd in ['claude', 'claude-jb']:
                check = subprocess.run(['which', cmd], capture_output=True, text=True)
                if check.returncode == 0:
                    claude_cmd = cmd
                    break
            else:
                # Claude Code not installed, simulate execution
                session.add_progress("Claude Code CLI not found - running in simulation mode")
                session.add_progress("Simulating agent execution...")

                # Simulate some work
                import time
                time.sleep(2)

                session.add_progress("Agent analyzed the task")
                session.add_progress("Generated solution")

                # Create a sample output file
                sample_file = workspace / 'agent_output.md'
                sample_file.write_text(f"""# Agent Output

## Task
{session.task}

## Analysis
The Claude Code agent analyzed your task and generated this response.

## Notes
- This is a simulation because Claude Code CLI is not installed
- To use the real agent, install claude-code in the container
- Model requested: {model}
- Environment: {environment}
""")

                session.files.append({
                    'path': str(sample_file),
                    'type': 'created',
                    'content': sample_file.read_text()
                })

                session.output = "Task completed in simulation mode"
                session.status = 'completed'
                session.completed_at = datetime.utcnow()
                session.add_progress("Task completed successfully (simulation)")
                return
        else:
            claude_cmd = 'claude-code'

        # Run Claude Code
        session.add_progress(f"Running {claude_cmd}...")

        # Build command
        cmd = [claude_cmd, '--print', session.task]

        process = subprocess.Popen(
            cmd,
            cwd=workspace,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        session.process = process

        output_lines = []
        for line in process.stdout:
            output_lines.append(line)
            session.add_progress(line.strip())

        process.wait()

        session.output = ''.join(output_lines)

        if process.returncode == 0:
            session.status = 'completed'
            session.add_progress("Task completed successfully")

            # If GitHub repo configured, commit and push changes
            if github_repo and github_token:
                session.add_progress("Committing changes to repository...")

                # Check for changes
                status = subprocess.run(['git', 'status', '--porcelain'], cwd=workspace, env=env, capture_output=True, text=True)
                if status.stdout.strip():
                    subprocess.run(['git', 'add', '.'], cwd=workspace, env=env, capture_output=True)
                    subprocess.run(['git', 'commit', '-m', f'Agent task: {session.task[:50]}...'], cwd=workspace, env=env, capture_output=True)
                    subprocess.run(['git', 'push'], cwd=workspace, env=env, capture_output=True)
                    session.add_progress("Changes pushed to repository")
                else:
                    session.add_progress("No changes to commit")
        else:
            session.status = 'error'
            session.error = f"Agent exited with code {process.returncode}"
            session.add_progress(f"Task failed: {session.error}")

    except Exception as e:
        session.status = 'error'
        session.error = str(e)
        session.add_progress(f"Error: {str(e)}")
        logger.error(f"Claude Code error: {traceback.format_exc()}")
    finally:
        session.completed_at = datetime.utcnow()


def run_codex_cli(session: AgentSession):
    """Execute task using Codex CLI agent"""
    try:
        session.status = 'running'
        session.add_progress("Initializing Codex CLI agent...")

        token = session.config.get('token')
        environment = session.config.get('environment', 'PREPROD')
        model = session.config.get('model')
        github_token = session.config.get('github_token')
        github_repo = session.config.get('github_repo')

        base_url = get_grazie_base_url(environment)

        # Set up environment for Codex CLI
        env = os.environ.copy()
        env['GRAZIE_API_TOKEN'] = token
        env['GRAZIE_ENVIRONMENT'] = environment

        if github_token:
            env['GITHUB_TOKEN'] = github_token
            session.add_progress("GitHub token configured for commit/push operations")

        # Create workspace directory
        workspace = Path('/workspace/agent-workspace')
        workspace.mkdir(parents=True, exist_ok=True)

        # If GitHub repo provided, clone it
        if github_repo:
            session.add_progress(f"Cloning repository: {github_repo}")
            repo_name = github_repo.split('/')[-1].replace('.git', '')
            repo_path = workspace / repo_name

            if repo_path.exists():
                session.add_progress("Repository already exists, pulling latest changes...")
                subprocess.run(['git', 'pull'], cwd=repo_path, env=env, capture_output=True)
            else:
                clone_url = github_repo
                if github_token and 'github.com' in github_repo:
                    clone_url = github_repo.replace('https://', f'https://{github_token}@')
                subprocess.run(['git', 'clone', clone_url], cwd=workspace, env=env, capture_output=True)

            workspace = repo_path

        session.add_progress(f"Working directory: {workspace}")
        session.add_progress(f"Executing task: {session.task}")

        # Check if codex is available
        codex_check = subprocess.run(['which', 'codex'], capture_output=True, text=True)

        if codex_check.returncode != 0:
            # Try alternative
            codex_jb_check = subprocess.run(['which', 'codex-jb'], capture_output=True, text=True)
            if codex_jb_check.returncode != 0:
                # Codex not installed, simulate execution
                session.add_progress("Codex CLI not found - running in simulation mode")
                session.add_progress("Simulating agent execution...")

                import time
                time.sleep(2)

                session.add_progress("Agent analyzed the task")
                session.add_progress("Generated solution")

                # Create a sample output file
                sample_file = workspace / 'codex_output.md'
                sample_file.write_text(f"""# Codex CLI Output

## Task
{session.task}

## Analysis
The Codex CLI agent analyzed your task and generated this response.

## Notes
- This is a simulation because Codex CLI is not installed
- To use the real agent, install codex in the container
- Environment: {environment}
""")

                session.files.append({
                    'path': str(sample_file),
                    'type': 'created',
                    'content': sample_file.read_text()
                })

                session.output = "Task completed in simulation mode"
                session.status = 'completed'
                session.completed_at = datetime.utcnow()
                session.add_progress("Task completed successfully (simulation)")
                return
            else:
                codex_cmd = 'codex-jb'
        else:
            codex_cmd = 'codex'

        # Run Codex
        session.add_progress(f"Running {codex_cmd}...")

        cmd = [codex_cmd, '-c', 'model_provider=jbai', session.task]

        process = subprocess.Popen(
            cmd,
            cwd=workspace,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        session.process = process

        output_lines = []
        for line in process.stdout:
            output_lines.append(line)
            session.add_progress(line.strip())

        process.wait()

        session.output = ''.join(output_lines)

        if process.returncode == 0:
            session.status = 'completed'
            session.add_progress("Task completed successfully")

            # If GitHub repo configured, commit and push changes
            if github_repo and github_token:
                session.add_progress("Committing changes to repository...")
                status = subprocess.run(['git', 'status', '--porcelain'], cwd=workspace, env=env, capture_output=True, text=True)
                if status.stdout.strip():
                    subprocess.run(['git', 'add', '.'], cwd=workspace, env=env, capture_output=True)
                    subprocess.run(['git', 'commit', '-m', f'Codex task: {session.task[:50]}...'], cwd=workspace, env=env, capture_output=True)
                    subprocess.run(['git', 'push'], cwd=workspace, env=env, capture_output=True)
                    session.add_progress("Changes pushed to repository")
                else:
                    session.add_progress("No changes to commit")
        else:
            session.status = 'error'
            session.error = f"Agent exited with code {process.returncode}"
            session.add_progress(f"Task failed: {session.error}")

    except Exception as e:
        session.status = 'error'
        session.error = str(e)
        session.add_progress(f"Error: {str(e)}")
        logger.error(f"Codex CLI error: {traceback.format_exc()}")
    finally:
        session.completed_at = datetime.utcnow()


def run_git_task(session: AgentSession):
    """Execute task with full Git integration - clone, branch, run agent, commit, push"""
    try:
        session.status = 'running'
        session.add_progress("Starting Git task execution...")

        token = session.config.get('token')
        environment = session.config.get('environment', 'PREPROD')
        model = session.config.get('model', 'claude-3-5-sonnet-20241022')
        git_token = session.config.get('github_token')
        git_repo_url = session.config.get('github_repo')
        branch_name = session.config.get('branch_name', 'agent-task')

        base_url = get_grazie_base_url(environment)

        # Set up environment
        env = os.environ.copy()
        env['GRAZIE_API_TOKEN'] = token
        env['GRAZIE_ENVIRONMENT'] = environment
        env['ANTHROPIC_API_KEY'] = 'use-grazie-token'
        env['ANTHROPIC_BASE_URL'] = f"{base_url}/anthropic/v1"
        env['GITHUB_TOKEN'] = git_token

        # Create workspace directory
        workspace = Path('/workspace/agent-workspace')
        workspace.mkdir(parents=True, exist_ok=True)

        # Clone repository
        session.add_progress(f"Cloning repository: {git_repo_url}")

        # Convert SSH URL to HTTPS URL if needed
        # SSH format: git@github.com:owner/repo.git
        # HTTPS format: https://github.com/owner/repo.git
        normalized_url = git_repo_url
        if git_repo_url.startswith('git@github.com:'):
            # Convert SSH to HTTPS
            repo_part = git_repo_url.replace('git@github.com:', '')
            normalized_url = f'https://github.com/{repo_part}'
            session.add_progress(f"Converted SSH URL to HTTPS: {normalized_url}")

        repo_name = normalized_url.split('/')[-1].replace('.git', '')
        repo_path = workspace / repo_name

        # Build authenticated clone URL
        clone_url = normalized_url
        if git_token and 'github.com' in normalized_url:
            clone_url = normalized_url.replace('https://', f'https://{git_token}@')

        if repo_path.exists():
            session.add_progress("Repository exists, fetching latest...")
            subprocess.run(['git', 'fetch', '--all'], cwd=repo_path, env=env, capture_output=True)
            subprocess.run(['git', 'checkout', 'main'], cwd=repo_path, env=env, capture_output=True)
            subprocess.run(['git', 'pull'], cwd=repo_path, env=env, capture_output=True)
        else:
            result = subprocess.run(['git', 'clone', clone_url], cwd=workspace, env=env, capture_output=True, text=True)
            if result.returncode != 0:
                session.add_progress(f"Clone failed: {result.stderr}")
                raise Exception(f"Failed to clone repository: {result.stderr}")
            session.add_progress("Repository cloned successfully")

        # Create and checkout branch
        session.add_progress(f"Creating branch: {branch_name}")
        subprocess.run(['git', 'checkout', '-B', branch_name], cwd=repo_path, env=env, capture_output=True)
        session.add_progress(f"Switched to branch: {branch_name}")

        # Configure git user for commits
        subprocess.run(['git', 'config', 'user.email', 'agent@orca-lab.local'], cwd=repo_path, env=env, capture_output=True)
        subprocess.run(['git', 'config', 'user.name', 'Orca Lab Agent'], cwd=repo_path, env=env, capture_output=True)

        session.add_progress(f"Using model: {model}")
        session.add_progress(f"Working directory: {repo_path}")
        session.add_progress(f"Executing task: {session.task}")

        # Check if claude-code is available
        claude_cmd = None
        for cmd in ['claude-code', 'claude', 'claude-jb']:
            check = subprocess.run(['which', cmd], capture_output=True, text=True)
            if check.returncode == 0:
                claude_cmd = cmd
                break

        if not claude_cmd:
            # Claude Code not installed, simulate execution
            session.add_progress("Claude Code CLI not found - running in simulation mode")
            session.add_progress("Simulating agent execution...")

            import time
            time.sleep(2)

            session.add_progress("Agent analyzed the task")
            session.add_progress("Generated solution")

            # Create a sample output file
            sample_file = repo_path / 'agent_output.md'
            sample_file.write_text(f"""# Agent Output

## Task
{session.task}

## Analysis
The Claude Code agent analyzed your task and generated this response.

## Notes
- This is a simulation because Claude Code CLI is not installed
- To use the real agent, install claude-code in the container
- Model requested: {model}
- Environment: {environment}
- Branch: {branch_name}
""")

            session.files.append({
                'path': str(sample_file),
                'type': 'created',
                'content': sample_file.read_text()
            })

            session.output = "Task completed in simulation mode"
        else:
            # Run Claude Code
            session.add_progress(f"Running {claude_cmd}...")

            cmd = [claude_cmd, '--print', session.task]

            process = subprocess.Popen(
                cmd,
                cwd=repo_path,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )

            session.process = process

            output_lines = []
            for line in process.stdout:
                output_lines.append(line)
                session.add_progress(line.strip())

            process.wait()

            session.output = ''.join(output_lines)

            if process.returncode != 0:
                session.add_progress(f"Agent exited with code {process.returncode}")

        # Check for changes and commit
        session.add_progress("Checking for changes...")
        status = subprocess.run(['git', 'status', '--porcelain'], cwd=repo_path, env=env, capture_output=True, text=True)

        if status.stdout.strip():
            session.add_progress("Changes detected, committing...")

            # Add all changes
            subprocess.run(['git', 'add', '.'], cwd=repo_path, env=env, capture_output=True)

            # Commit
            commit_msg = f"Agent task: {session.task[:50]}..."
            commit_result = subprocess.run(
                ['git', 'commit', '-m', commit_msg],
                cwd=repo_path, env=env, capture_output=True, text=True
            )

            if commit_result.returncode == 0:
                session.add_progress("Changes committed")

                # Push to remote
                session.add_progress(f"Pushing to branch: {branch_name}")
                push_result = subprocess.run(
                    ['git', 'push', '-u', 'origin', branch_name, '--force'],
                    cwd=repo_path, env=env, capture_output=True, text=True
                )

                if push_result.returncode == 0:
                    session.add_progress(f"Successfully pushed to {branch_name}")

                    # Extract the PR URL hint
                    pr_url = f"{git_repo_url.replace('.git', '')}/compare/{branch_name}?expand=1"
                    session.add_progress(f"Create PR: {pr_url}")
                else:
                    session.add_progress(f"Push failed: {push_result.stderr}")
            else:
                session.add_progress(f"Commit failed: {commit_result.stderr}")
        else:
            session.add_progress("No changes to commit")

        session.status = 'completed'
        session.add_progress("Git task completed successfully")

    except Exception as e:
        session.status = 'error'
        session.error = str(e)
        session.add_progress(f"Error: {str(e)}")
        logger.error(f"Git task error: {traceback.format_exc()}")
    finally:
        session.completed_at = datetime.utcnow()


@app.route('/')
def index():
    return jsonify({
        'service': 'agent-service',
        'version': '1.1.0',
        'status': 'running',
        'endpoints': {
            '/api/agent/git-task': 'POST - Execute task with Git integration (clone, branch, commit, push)',
            '/api/agent/execute': 'POST - Execute agent task',
            '/api/agent/status/<session_id>': 'GET - Get session status',
            '/api/agent/stop/<session_id>': 'POST - Stop agent session',
            '/api/agent/files/<session_id>': 'GET - Get changed files',
            '/api/agent/sessions': 'GET - List all sessions'
        }
    })


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint for orca-lab connectivity"""
    import platform
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'container': os.environ.get('CONTAINER_NAME', 'agent'),
        'hostname': platform.node(),
        'python_version': platform.python_version(),
        'service': 'agent-service',
        'port': 8001,
        'active_sessions': len(sessions)
    })


@app.route('/api/agent/git-task', methods=['POST'])
def git_task():
    """Start agent task with Git integration - clones repo, creates branch, runs task, commits and pushes.

    This endpoint is called by the orca-lab Agent tab to execute tasks on a Git repository.
    """
    try:
        data = request.get_json()

        token = data.get('token')
        environment = data.get('environment', 'PREPROD')
        model = data.get('model', 'claude-3-5-sonnet-20241022')
        task = data.get('task')
        git_repo_url = data.get('git_repo_url')
        git_token = data.get('git_token')
        branch_name = data.get('branch_name')

        logger.info(f"=== GIT-TASK REQUEST ===")
        logger.info(f"Environment: {environment}")
        logger.info(f"Model: {model}")
        logger.info(f"Task: {task[:100] if task else 'None'}...")
        logger.info(f"Git Repo: {git_repo_url or 'Not configured'}")
        logger.info(f"Branch: {branch_name or 'Not specified'}")

        if not token:
            return jsonify({'error': 'Token is required'}), 400

        if not task:
            return jsonify({'error': 'Task is required'}), 400

        if not git_repo_url:
            return jsonify({'error': 'Git repository URL is required'}), 400

        if not git_token:
            return jsonify({'error': 'Git token is required'}), 400

        # Create session with git configuration
        session_id = str(uuid.uuid4())
        config = {
            'token': token,
            'environment': environment,
            'model': model,
            'github_token': git_token,
            'github_repo': git_repo_url,
            'branch_name': branch_name or 'agent-task'
        }

        session = AgentSession(session_id, 'claude', task, config)
        sessions[session_id] = session

        # Start git task in background thread
        thread = threading.Thread(target=run_git_task, args=(session,))
        thread.daemon = True
        thread.start()

        return jsonify({
            'session_id': session_id,
            'agent': 'claude',
            'status': 'started',
            'message': 'Git task started - cloning repo and executing agent'
        })

    except Exception as e:
        logger.error(f"Git task error: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/agent/execute', methods=['POST'])
def execute_agent():
    """Start agent execution for a task"""
    try:
        data = request.get_json()

        token = data.get('token')
        environment = data.get('environment', 'PREPROD')
        model = data.get('model', 'claude-3-5-sonnet-20241022')
        task = data.get('task')
        agent = data.get('agent', 'claude')
        github_token = data.get('github_token')
        github_repo = data.get('github_repo')

        logger.info(f"=== AGENT EXECUTE REQUEST ===")
        logger.info(f"Agent: {agent}")
        logger.info(f"Environment: {environment}")
        logger.info(f"Model: {model}")
        logger.info(f"Task: {task[:100] if task else 'None'}...")
        logger.info(f"GitHub Repo: {github_repo or 'Not configured'}")

        if not token:
            return jsonify({'error': 'Token is required'}), 400

        if not task:
            return jsonify({'error': 'Task is required'}), 400

        # Create session
        session_id = str(uuid.uuid4())
        config = {
            'token': token,
            'environment': environment,
            'model': model,
            'github_token': github_token,
            'github_repo': github_repo
        }

        session = AgentSession(session_id, agent, task, config)
        sessions[session_id] = session

        # Start agent in background thread
        if agent == 'claude':
            thread = threading.Thread(target=run_claude_code, args=(session,))
        else:
            thread = threading.Thread(target=run_codex_cli, args=(session,))

        thread.daemon = True
        thread.start()

        return jsonify({
            'session_id': session_id,
            'agent': agent,
            'status': 'started',
            'message': f'{agent.title()} agent started'
        })

    except Exception as e:
        logger.error(f"Execute error: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/agent/status/<session_id>', methods=['GET'])
def get_status(session_id):
    """Get status of an agent session"""
    try:
        session = sessions.get(session_id)

        if not session:
            return jsonify({'error': 'Session not found'}), 404

        # Return only new progress since last check
        response = session.to_dict()

        return jsonify(response)

    except Exception as e:
        logger.error(f"Status error: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/agent/stop/<session_id>', methods=['POST'])
def stop_agent(session_id):
    """Stop a running agent session"""
    try:
        session = sessions.get(session_id)

        if not session:
            return jsonify({'error': 'Session not found'}), 404

        if session.process:
            session.process.terminate()
            session.add_progress("Agent stopped by user")

        session.status = 'stopped'
        session.completed_at = datetime.utcnow()

        return jsonify({
            'session_id': session_id,
            'status': 'stopped',
            'message': 'Agent stopped'
        })

    except Exception as e:
        logger.error(f"Stop error: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/agent/files/<session_id>', methods=['GET'])
def get_files(session_id):
    """Get files changed by the agent"""
    try:
        session = sessions.get(session_id)

        if not session:
            return jsonify({'error': 'Session not found'}), 404

        return jsonify({
            'session_id': session_id,
            'files': session.files
        })

    except Exception as e:
        logger.error(f"Files error: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/agent/sessions', methods=['GET'])
def list_sessions():
    """List all agent sessions"""
    try:
        return jsonify({
            'sessions': [s.to_dict() for s in sessions.values()]
        })
    except Exception as e:
        logger.error(f"List sessions error: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500


@app.errorhandler(Exception)
def handle_exception(e):
    logger.error(f"Unhandled exception: {str(e)}\n{traceback.format_exc()}")
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    logger.info("="*60)
    logger.info("Starting Agent Service")
    logger.info("="*60)
    logger.info("Web Interface: http://localhost:8001")
    logger.info("="*60)

    app.run(debug=True, host='0.0.0.0', port=8001)

/**
 * Unified Service for Orca AI Workload Containers
 *
 * This service provides:
 * - Chat Service (Port 8000): AI chat through JetBrains Grazie platform
 * - Agent Service (Port 8001): Git workflow automation with Claude Code
 * - IDE Service (Port 8080): code-server status endpoints
 *
 * The service runs as a single process with PORT env var determining behavior.
 */

const express = require('express');
const axios = require('axios');
const { v4: uuidv4 } = require('uuid');
const { exec, spawn } = require('child_process');
const fs = require('fs').promises;
const path = require('path');
const os = require('os');

const app = express();

// Parse JSON bodies
app.use(express.json());

// Enable CORS for all routes - required for orca-lab proxy access
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.header('Access-Control-Allow-Headers', 'Content-Type, Authorization, Grazie-Authenticate-JWT');
  res.header('Access-Control-Allow-Credentials', 'true');
  if (req.method === 'OPTIONS') {
    return res.sendStatus(200);
  }
  next();
});

// ============================================================================
// Configuration
// ============================================================================

const PORT = parseInt(process.env.PORT || '8000');
const CONTAINER_NAME = process.env.CONTAINER_NAME || 'unknown';

// JetBrains AI Platform (Grazie) endpoints
const GRAZIE_ENDPOINTS = {
  'PREPROD': 'https://api-preprod.jetbrains.ai/user/v5/llm',
  'PRODUCTION': 'https://api.jetbrains.ai/user/v5/llm',
  'STAGING': 'https://api.stgn.jetbrains.ai/user/v5/llm'
};

// Anthropic API endpoints via Grazie
const ANTHROPIC_ENDPOINTS = {
  'PREPROD': 'https://api-preprod.jetbrains.ai/user/v5/llm/anthropic/v1',
  'PRODUCTION': 'https://api.jetbrains.ai/user/v5/llm/anthropic/v1',
  'STAGING': 'https://api.stgn.jetbrains.ai/user/v5/llm/anthropic/v1'
};

// In-memory storage
const conversations = new Map();
const agentSessions = new Map();

// ============================================================================
// Utility Functions
// ============================================================================

function log(message) {
  console.log(`[${new Date().toISOString()}] ${message}`);
}

function getTimestamp() {
  return new Date().toISOString();
}

/**
 * Run a shell command and return output
 */
function runCommand(cmd, cwd = null, env = null, timeout = 300000) {
  return new Promise((resolve) => {
    const options = {
      shell: true,
      cwd: cwd || process.cwd(),
      env: env || process.env,
      timeout: timeout
    };

    exec(cmd, options, (error, stdout, stderr) => {
      const output = stdout + stderr;
      if (error) {
        resolve({ success: false, output: output || error.message });
      } else {
        resolve({ success: true, output });
      }
    });
  });
}

/**
 * Get list of changed files in a git repo
 */
async function getChangedFiles(repoPath) {
  const files = [];
  const result = await runCommand(
    'git diff --name-status HEAD~1 HEAD 2>/dev/null || git diff --name-status HEAD',
    repoPath
  );

  if (result.success && result.output.trim()) {
    const lines = result.output.trim().split('\n');
    for (const line of lines) {
      if (!line) continue;
      const parts = line.split('\t');
      if (parts.length >= 2) {
        const status = parts[0];
        const filepath = parts[1];
        let fileType = 'modified';
        if (status.startsWith('A')) fileType = 'created';
        else if (status.startsWith('D')) fileType = 'deleted';

        let content = null;
        if (fileType !== 'deleted') {
          try {
            const fullPath = path.join(repoPath, filepath);
            const stats = await fs.stat(fullPath);
            if (stats.size < 10000) {
              content = await fs.readFile(fullPath, 'utf-8');
            }
          } catch (e) {
            // Ignore read errors
          }
        }

        files.push({ path: filepath, type: fileType, content });
      }
    }
  }
  return files;
}

// ============================================================================
// Health Endpoints (All Ports)
// ============================================================================

app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    timestamp: getTimestamp(),
    container: CONTAINER_NAME,
    hostname: os.hostname(),
    nodeVersion: process.version,
    port: PORT,
    service: PORT === 8000 ? 'chat' : PORT === 8001 ? 'agent' : 'ide',
    ai_enabled: true
  });
});

app.get('/api/health', (req, res) => {
  res.json({
    status: 'healthy',
    timestamp: getTimestamp(),
    container: CONTAINER_NAME,
    hostname: os.hostname(),
    nodeVersion: process.version,
    port: PORT,
    service: PORT === 8000 ? 'chat' : PORT === 8001 ? 'agent' : 'ide',
    ai_enabled: true
  });
});

// ============================================================================
// Chat Service Endpoints (Port 8000)
// ============================================================================

/**
 * Simple chat endpoint that echoes messages back
 */
app.post('/chat', (req, res) => {
  try {
    const { message = '', session_id = uuidv4() } = req.body;

    if (!conversations.has(session_id)) {
      conversations.set(session_id, []);
    }

    const conversation = conversations.get(session_id);
    conversation.push({
      role: 'user',
      message,
      timestamp: getTimestamp()
    });

    const responseText = `Hello! You said: ${message}`;

    conversation.push({
      role: 'assistant',
      message: responseText,
      timestamp: getTimestamp()
    });

    res.json({
      response: responseText,
      session_id,
      timestamp: getTimestamp(),
      metadata: {
        message_length: message.length,
        service: CONTAINER_NAME
      }
    });
  } catch (error) {
    log(`[Chat] Error: ${error.message}`);
    res.status(500).json({ error: error.message });
  }
});

/**
 * AI chat endpoint with JetBrains AI Platform integration
 */
app.post('/api/chat', async (req, res) => {
  try {
    const {
      token = '',
      environment = 'PREPROD',
      model = 'anthropic/claude-3-5-sonnet',
      message = '',
      stream = false
    } = req.body;

    if (!token) {
      return res.status(400).json({ error: 'Token is required' });
    }
    if (!message) {
      return res.status(400).json({ error: 'Message is required' });
    }

    const baseUrl = GRAZIE_ENDPOINTS[environment] || GRAZIE_ENDPOINTS['PREPROD'];
    let apiPath, grazieRequest;

    if (model.startsWith('anthropic/')) {
      apiPath = '/anthropic/v1/messages';
      grazieRequest = {
        model: model.replace('anthropic/', ''),
        messages: [{ role: 'user', content: message }],
        max_tokens: 4096,
        stream
      };
    } else if (model.startsWith('openai/')) {
      apiPath = '/openai/v1/chat/completions';
      grazieRequest = {
        model: model.replace('openai/', ''),
        messages: [{ role: 'user', content: message }],
        stream
      };
    } else {
      apiPath = '/anthropic/v1/messages';
      grazieRequest = {
        model: 'claude-3-5-sonnet-20241022',
        messages: [{ role: 'user', content: message }],
        max_tokens: 4096,
        stream
      };
    }

    const fullUrl = `${baseUrl}${apiPath}`;
    log(`[AI Chat] Calling ${fullUrl} with model ${model}`);

    const response = await axios.post(fullUrl, grazieRequest, {
      headers: {
        'Content-Type': 'application/json',
        'Grazie-Authenticate-JWT': token
      },
      timeout: 60000
    });

    const aiResponse = response.data;
    let responseText;

    if (aiResponse.content && Array.isArray(aiResponse.content)) {
      // Anthropic format
      responseText = aiResponse.content[0]?.text || '';
    } else if (aiResponse.choices && aiResponse.choices.length > 0) {
      // OpenAI format
      responseText = aiResponse.choices[0].message.content;
    } else {
      responseText = JSON.stringify(aiResponse);
    }

    res.json({
      response: responseText,
      timestamp: getTimestamp(),
      model,
      environment
    });
  } catch (error) {
    log(`[AI Chat] Error: ${error.message}`);
    if (error.code === 'ECONNABORTED') {
      return res.status(504).json({ error: 'Request timeout' });
    }
    if (error.response) {
      return res.status(error.response.status).json({
        error: `AI Platform request failed: ${error.response.status}`,
        details: error.response.data
      });
    }
    res.status(500).json({ error: `Network error: ${error.message}` });
  }
});

/**
 * Get available models from JetBrains AI Platform
 */
app.post('/api/models', async (req, res) => {
  try {
    const { token = '', environment = 'PREPROD' } = req.body;

    if (!token) {
      return res.status(400).json({ error: 'Token is required' });
    }

    const baseUrl = GRAZIE_ENDPOINTS[environment] || GRAZIE_ENDPOINTS['PREPROD'];
    const fullUrl = `${baseUrl}/openai/v1/models`;

    log(`[Models] Fetching from ${fullUrl}`);

    try {
      const response = await axios.get(fullUrl, {
        headers: { 'Grazie-Authenticate-JWT': token },
        timeout: 10000
      });

      const modelsData = response.data;
      const models = [];

      if (modelsData.data && Array.isArray(modelsData.data)) {
        for (const model of modelsData.data) {
          let modelId = model.id || '';
          if (!modelId.startsWith('anthropic/') && !modelId.startsWith('openai/')) {
            modelId = `openai/${modelId}`;
          }
          models.push({
            id: modelId,
            name: model.name || modelId,
            provider: modelId.includes('/') ? modelId.split('/')[0].charAt(0).toUpperCase() + modelId.split('/')[0].slice(1) : 'Unknown'
          });
        }
      }

      res.json({ models, timestamp: getTimestamp() });
    } catch (apiError) {
      log(`[Models] API call failed, returning defaults`);
      res.json({
        models: [
          { id: 'anthropic/claude-3-5-sonnet-20241022', name: 'Claude 3.5 Sonnet', provider: 'Anthropic' },
          { id: 'anthropic/claude-3-5-haiku-20241022', name: 'Claude 3.5 Haiku', provider: 'Anthropic' },
          { id: 'openai/gpt-4o', name: 'GPT-4o', provider: 'OpenAI' },
          { id: 'openai/gpt-4o-mini', name: 'GPT-4o Mini', provider: 'OpenAI' }
        ],
        timestamp: getTimestamp()
      });
    }
  } catch (error) {
    log(`[Models] Error: ${error.message}`);
    res.status(500).json({ error: error.message });
  }
});

/**
 * Validate JetBrains AI Platform token
 */
app.post('/api/validate_token', async (req, res) => {
  try {
    const { token = '', environment = 'PREPROD' } = req.body;

    if (!token) {
      return res.status(400).json({ valid: false, error: 'No token provided' });
    }

    const baseUrl = GRAZIE_ENDPOINTS[environment] || GRAZIE_ENDPOINTS['PREPROD'];
    const fullUrl = `${baseUrl}/openai/v1/models`;

    log(`[Validate] Testing token against ${fullUrl}`);

    try {
      await axios.get(fullUrl, {
        headers: { 'Grazie-Authenticate-JWT': token },
        timeout: 10000
      });

      res.json({
        valid: true,
        timestamp: getTimestamp(),
        environment
      });
    } catch (apiError) {
      log(`[Validate] Token invalid: ${apiError.response?.status || 'unknown'}`);
      res.status(401).json({
        valid: false,
        error: `Token validation failed: ${apiError.response?.status || 'unknown'}`,
        details: apiError.response?.data
      });
    }
  } catch (error) {
    log(`[Validate] Error: ${error.message}`);
    res.status(500).json({ valid: false, error: `Network error: ${error.message}` });
  }
});

// ============================================================================
// Agent Service Endpoints (Port 8001)
// ============================================================================

/**
 * Call Claude API via Grazie to get suggestions
 */
async function callAnthropicApi(token, environment, model, task, repoPath) {
  try {
    const baseUrl = ANTHROPIC_ENDPOINTS[environment] || ANTHROPIC_ENDPOINTS['STAGING'];

    // Get some context from the repository
    const contextFiles = [];
    try {
      const files = await fs.readdir(repoPath);
      for (const f of files.slice(0, 10)) {
        try {
          const filepath = path.join(repoPath, f);
          const stats = await fs.stat(filepath);
          if (stats.isFile() && stats.size < 5000) {
            const content = await fs.readFile(filepath, 'utf-8');
            contextFiles.push(`File: ${f}\n\`\`\`\n${content}\n\`\`\``);
          }
        } catch (e) {
          // Skip unreadable files
        }
      }
    } catch (e) {
      // Skip if directory read fails
    }

    const context = contextFiles.slice(0, 5).join('\n\n');

    const prompt = `You are a coding assistant. Based on the following task and repository context, provide specific code changes.

Task: ${task}

Repository Context:
${context}

Provide your response as specific file modifications. For each file, use this format:
FILE: path/to/file
\`\`\`
new file content
\`\`\`

Only include files that need to be modified or created.`;

    const response = await axios.post(
      `${baseUrl}/messages`,
      {
        model,
        max_tokens: 4000,
        messages: [{ role: 'user', content: prompt }]
      },
      {
        headers: {
          'Content-Type': 'application/json',
          'Grazie-Authenticate-JWT': token,
          'anthropic-version': '2023-06-01'
        },
        timeout: 120000
      }
    );

    if (response.data.content && response.data.content.length > 0) {
      return response.data.content[0].text || '';
    }
    return null;
  } catch (error) {
    log(`[Anthropic API] Error: ${error.message}`);
    return null;
  }
}

/**
 * Parse and apply Claude's suggestions to the repository
 */
async function applyClaudeSuggestions(repoPath, responseText, session) {
  try {
    const filePattern = /FILE:\s*(.+?)\n```(?:\w+)?\n([\s\S]*?)```/g;
    let match;
    let applied = false;

    while ((match = filePattern.exec(responseText)) !== null) {
      const filepath = match[1].trim();
      const content = match[2].trim();

      const fullPath = path.join(repoPath, filepath);

      // Create directory if needed
      await fs.mkdir(path.dirname(fullPath), { recursive: true });

      // Write the file
      await fs.writeFile(fullPath, content);
      session.progress.push(`Modified: ${filepath}`);
      applied = true;
    }

    if (!applied) {
      session.progress.push('No file changes detected in response');
    }
  } catch (error) {
    session.progress.push(`Error applying changes: ${error.message}`);
  }
}

/**
 * Execute the full Git workflow with Claude Code
 */
async function executeGitTask(sessionId, token, environment, model, task, gitRepoUrl, gitToken, branchName) {
  const session = agentSessions.get(sessionId);
  if (!session) return;

  let tempDir = null;

  try {
    // Step 1: Create temp directory
    session.progress.push('Creating temporary workspace...');
    tempDir = await fs.mkdtemp(path.join(os.tmpdir(), 'claude-agent-'));
    session.temp_dir = tempDir;

    // Step 2: Clone repository
    session.progress.push('Cloning repository...');
    session.git_status.cloning = true;

    // Prepare clone URL with authentication
    let cloneUrl = gitRepoUrl;
    if (gitToken && gitRepoUrl.includes('github.com')) {
      if (gitRepoUrl.startsWith('git@github.com:')) {
        const repoPath = gitRepoUrl.replace('git@github.com:', '').replace('.git', '');
        cloneUrl = `https://${gitToken}@github.com/${repoPath}.git`;
      } else if (gitRepoUrl.startsWith('https://github.com/')) {
        cloneUrl = gitRepoUrl.replace('https://github.com/', `https://${gitToken}@github.com/`);
      }
    }

    const repoDir = path.join(tempDir, 'repo');
    let result = await runCommand(`git clone --depth=50 "${cloneUrl}" repo`, tempDir);
    if (!result.success) {
      throw new Error(`Failed to clone repository: ${result.output}`);
    }

    session.git_status.cloned = true;
    session.progress.push('Repository cloned successfully');

    // Step 3: Configure git
    session.progress.push('Configuring git...');
    await runCommand('git config user.email "claude-agent@orca-lab.local"', repoDir);
    await runCommand('git config user.name "Claude Agent"', repoDir);

    // Step 4: Create branch
    session.progress.push(`Creating branch: ${branchName}`);
    result = await runCommand(`git checkout -b "${branchName}"`, repoDir);
    if (!result.success) {
      throw new Error(`Failed to create branch: ${result.output}`);
    }
    session.git_status.branch_created = true;

    // Step 5: Execute Claude via Grazie API
    session.progress.push('Executing Claude agent via Grazie API...');
    session.progress.push(`Task: ${task}`);
    session.progress.push(`Environment: ${environment}`);
    session.progress.push(`Model: ${model}`);

    // Call Anthropic API directly via Grazie proxy (more reliable than CLI in containers)
    const apiResponse = await callAnthropicApi(token, environment, model, task, repoDir);
    if (apiResponse) {
      session.progress.push('Received response from Claude API');
      await applyClaudeSuggestions(repoDir, apiResponse, session);
    } else {
      session.progress.push('Warning: Could not get response from API');
    }

    // Step 6: Check for changes
    session.progress.push('Checking for changes...');
    result = await runCommand('git status --porcelain', repoDir);

    if (result.output.trim()) {
      // There are changes to commit
      session.progress.push('Changes detected, staging files...');
      await runCommand('git add -A', repoDir);

      // Step 7: Commit changes
      const commitMsg = task.length > 50 ? `Claude Agent: ${task.substring(0, 50)}...` : `Claude Agent: ${task}`;
      result = await runCommand(`git commit -m "${commitMsg.replace(/"/g, '\\"')}"`, repoDir);

      if (result.success) {
        session.git_status.committed = true;
        session.progress.push('Changes committed');

        // Get changed files
        session.files = await getChangedFiles(repoDir);

        // Step 8: Push to remote
        session.progress.push(`Pushing branch ${branchName} to remote...`);
        result = await runCommand(`git push -u origin "${branchName}"`, repoDir);

        if (result.success) {
          session.git_status.pushed = true;
          session.progress.push(`Branch ${branchName} pushed successfully`);
        } else {
          session.progress.push(`Warning: Push failed - ${result.output}`);
        }
      } else {
        session.progress.push('No changes to commit');
      }
    } else {
      session.progress.push('No changes were made by the agent');
    }

    // Mark as completed
    session.status = 'completed';
    session.progress.push('Task completed successfully!');

  } catch (error) {
    session.status = 'error';
    session.error = error.message;
    session.progress.push(`Error: ${error.message}`);
    log(`[Git Task] Error: ${error.message}`);
  } finally {
    // Cleanup temp directory (delayed to allow file reading)
    if (tempDir) {
      setTimeout(async () => {
        try {
          await fs.rm(tempDir, { recursive: true, force: true });
        } catch (e) {
          // Ignore cleanup errors
        }
      }, 60000);
    }
  }
}

/**
 * Execute a Git-based task with Claude Code
 */
app.post('/api/agent/git-task', (req, res) => {
  try {
    const {
      token = '',
      environment = 'STAGING',
      model = 'claude-sonnet-4-5-20250929',
      task = '',
      git_repo_url = '',
      git_token = '',
      branch_name = ''
    } = req.body;

    // Validation
    if (!token) {
      return res.status(400).json({ error: 'Grazie token is required' });
    }
    if (!task) {
      return res.status(400).json({ error: 'Task description is required' });
    }
    if (!git_repo_url) {
      return res.status(400).json({ error: 'Git repository URL is required' });
    }

    const finalBranchName = branch_name || `claude-agent/${new Date().toISOString().replace(/[:.]/g, '-').substring(0, 19)}`;

    // Create session
    const sessionId = uuidv4();
    agentSessions.set(sessionId, {
      task,
      model,
      environment,
      status: 'running',
      created_at: getTimestamp(),
      branch_name: finalBranchName,
      git_repo_url,
      progress: [],
      git_status: {
        cloning: false,
        cloned: false,
        branch_created: false,
        committed: false,
        pushed: false
      },
      files: [],
      error: null
    });

    // Start background task
    executeGitTask(sessionId, token, environment, model, task, git_repo_url, git_token, finalBranchName);

    res.json({
      session_id: sessionId,
      status: 'running',
      branch_name: finalBranchName,
      timestamp: getTimestamp()
    });
  } catch (error) {
    log(`[Git Task] Error: ${error.message}`);
    res.status(500).json({ error: error.message });
  }
});

/**
 * Start an agent session (legacy endpoint)
 */
app.post('/api/agent/start', (req, res) => {
  try {
    const {
      token = '',
      environment = 'PREPROD',
      model = 'claude-sonnet-4-5-20250929',
      task = ''
    } = req.body;

    if (!token) {
      return res.status(400).json({ error: 'Token is required' });
    }
    if (!task) {
      return res.status(400).json({ error: 'Task is required' });
    }

    // Create agent session
    const sessionId = uuidv4();
    agentSessions.set(sessionId, {
      task,
      model,
      environment,
      status: 'running',
      created_at: getTimestamp(),
      progress: [],
      messages: []
    });

    res.json({
      session_id: sessionId,
      status: 'running',
      timestamp: getTimestamp()
    });
  } catch (error) {
    log(`[Agent Start] Error: ${error.message}`);
    res.status(500).json({ error: error.message });
  }
});

/**
 * Get agent session status
 */
app.get('/api/agent/status/:session_id', (req, res) => {
  const { session_id } = req.params;

  if (!agentSessions.has(session_id)) {
    return res.status(404).json({ error: 'Session not found' });
  }

  const session = agentSessions.get(session_id);

  const responseData = {
    session_id,
    status: session.status,
    task: session.task,
    created_at: session.created_at,
    timestamp: getTimestamp()
  };

  // Include git-specific fields if present
  if (session.git_status) {
    responseData.git_status = session.git_status;
  }
  if (session.branch_name) {
    responseData.branch_name = session.branch_name;
  }
  if (session.files) {
    responseData.files = session.files;
  }
  if (session.error) {
    responseData.error = session.error;
  }
  if (session.progress && session.progress.length > 0) {
    responseData.progress = session.progress;
  }

  res.json(responseData);
});

/**
 * Get files changed by the agent
 */
app.get('/api/agent/files/:session_id', (req, res) => {
  const { session_id } = req.params;

  if (!agentSessions.has(session_id)) {
    return res.status(404).json({ error: 'Session not found' });
  }

  const session = agentSessions.get(session_id);
  res.json({
    session_id,
    files: session.files || [],
    timestamp: getTimestamp()
  });
});

/**
 * Stop an agent session
 */
app.post('/api/agent/stop/:session_id', (req, res) => {
  const { session_id } = req.params;

  if (!agentSessions.has(session_id)) {
    return res.status(404).json({ error: 'Session not found' });
  }

  const session = agentSessions.get(session_id);
  session.status = 'stopped';

  res.json({
    session_id,
    status: 'stopped',
    timestamp: getTimestamp()
  });
});

// ============================================================================
// IDE Service Endpoints (Port 8080)
// ============================================================================

app.get('/ide/healthz', (req, res) => {
  res.json({
    status: 'healthy',
    service: 'ide',
    codeServerRunning: true,
    timestamp: getTimestamp()
  });
});

app.get('/ide/status', (req, res) => {
  res.json({
    status: 'running',
    service: 'ide',
    port: 8080,
    timestamp: getTimestamp()
  });
});

// Legacy agent endpoints for compatibility
app.get('/agent/health', (req, res) => {
  res.json({
    status: 'healthy',
    service: 'agent',
    port: PORT,
    timestamp: getTimestamp()
  });
});

app.post('/agent/execute', (req, res) => {
  const { command = '' } = req.body;
  res.json({
    message: 'Agent execution endpoint',
    command,
    status: 'ready',
    claudeCodeAvailable: false,
    service: 'agent',
    timestamp: getTimestamp()
  });
});

app.get('/agent/status', (req, res) => {
  res.json({
    status: 'running',
    service: 'agent',
    port: PORT,
    timestamp: getTimestamp()
  });
});

// ============================================================================
// Graceful Shutdown
// ============================================================================

process.on('SIGTERM', () => {
  log('Received SIGTERM, shutting down gracefully...');
  process.exit(0);
});

process.on('SIGINT', () => {
  log('Received SIGINT, shutting down gracefully...');
  process.exit(0);
});

// ============================================================================
// Start Server
// ============================================================================

app.listen(PORT, '0.0.0.0', () => {
  log('========================================');
  log(`Unified Service (Node.js) started`);
  log(`Listening on port ${PORT}`);
  log(`Container: ${CONTAINER_NAME}`);
  log('========================================');
  log('Available endpoints:');
  log('  GET  /health              - Service health');
  log('  GET  /api/health          - API health');
  if (PORT === 8000) {
    log('  POST /chat                - Simple chat');
    log('  POST /api/chat            - AI chat (Grazie)');
    log('  POST /api/models          - Get available models');
    log('  POST /api/validate_token  - Validate token');
  }
  if (PORT === 8001) {
    log('  POST /api/agent/start     - Start agent session');
    log('  POST /api/agent/git-task  - Execute Git task');
    log('  GET  /api/agent/status/:id - Get session status');
    log('  GET  /api/agent/files/:id  - Get changed files');
    log('  POST /api/agent/stop/:id   - Stop session');
  }
  log('========================================');
});

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
const http = require('http');
const { WebSocketServer } = require('ws');

const app = express();
const server = http.createServer(app);

// WebSocket server for real-time agent updates
const wss = new WebSocketServer({ noServer: true });

// Track WebSocket clients by session ID
const sessionClients = new Map(); // sessionId -> Set<ws>

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
const qaCellSessions = new Map();

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
async function applyClaudeSuggestions(repoPath, responseText, session, sessionId) {
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
      const msg = `Modified: ${filepath}`;
      session.progress.push(msg);
      broadcastProgress(sessionId, msg);
      applied = true;
    }

    if (!applied) {
      const msg = 'No file changes detected in response';
      session.progress.push(msg);
      broadcastProgress(sessionId, msg);
    }
  } catch (error) {
    const msg = `Error applying changes: ${error.message}`;
    session.progress.push(msg);
    broadcastProgress(sessionId, msg);
  }
}

/**
 * Helper to push progress and broadcast
 */
function pushProgress(session, sessionId, message) {
  session.progress.push(message);
  broadcastProgress(sessionId, message);
}

/**
 * Helper to update status and broadcast full state
 */
function updateStatus(session, sessionId, status) {
  session.status = status;
  broadcastStatus(sessionId, {
    status: session.status,
    progress: session.progress || [],
    gitStatus: session.git_status || {},
    files: session.files || [],
    error: session.error,
  });
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
    pushProgress(session, sessionId, 'Creating temporary workspace...');
    tempDir = await fs.mkdtemp(path.join(os.tmpdir(), 'claude-agent-'));
    session.temp_dir = tempDir;

    // Step 2: Clone repository
    pushProgress(session, sessionId, 'Cloning repository...');
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
    pushProgress(session, sessionId, 'Repository cloned successfully');

    // Step 3: Configure git
    pushProgress(session, sessionId, 'Configuring git...');
    await runCommand('git config user.email "claude-agent@orca-lab.local"', repoDir);
    await runCommand('git config user.name "Claude Agent"', repoDir);

    // Step 4: Create branch
    pushProgress(session, sessionId, `Creating branch: ${branchName}`);
    result = await runCommand(`git checkout -b "${branchName}"`, repoDir);
    if (!result.success) {
      throw new Error(`Failed to create branch: ${result.output}`);
    }
    session.git_status.branch_created = true;

    // Step 5: Execute Claude via Grazie API
    pushProgress(session, sessionId, 'Executing Claude agent via Grazie API...');
    pushProgress(session, sessionId, `Task: ${task}`);
    pushProgress(session, sessionId, `Environment: ${environment}`);
    pushProgress(session, sessionId, `Model: ${model}`);

    // Call Anthropic API directly via Grazie proxy (more reliable than CLI in containers)
    const apiResponse = await callAnthropicApi(token, environment, model, task, repoDir);
    if (apiResponse) {
      pushProgress(session, sessionId, 'Received response from Claude API');
      await applyClaudeSuggestions(repoDir, apiResponse, session, sessionId);
    } else {
      pushProgress(session, sessionId, 'Warning: Could not get response from API');
    }

    // Step 6: Check for changes
    pushProgress(session, sessionId, 'Checking for changes...');
    result = await runCommand('git status --porcelain', repoDir);

    if (result.output.trim()) {
      // There are changes to commit
      pushProgress(session, sessionId, 'Changes detected, staging files...');
      await runCommand('git add -A', repoDir);

      // Step 7: Commit changes
      const commitMsg = task.length > 50 ? `Claude Agent: ${task.substring(0, 50)}...` : `Claude Agent: ${task}`;
      result = await runCommand(`git commit -m "${commitMsg.replace(/"/g, '\\"')}"`, repoDir);

      if (result.success) {
        session.git_status.committed = true;
        pushProgress(session, sessionId, 'Changes committed');

        // Get changed files
        session.files = await getChangedFiles(repoDir);

        // Step 8: Push to remote
        pushProgress(session, sessionId, `Pushing branch ${branchName} to remote...`);
        result = await runCommand(`git push -u origin "${branchName}"`, repoDir);

        if (result.success) {
          session.git_status.pushed = true;
          pushProgress(session, sessionId, `Branch ${branchName} pushed successfully`);
        } else {
          pushProgress(session, sessionId, `Warning: Push failed - ${result.output}`);
        }
      } else {
        pushProgress(session, sessionId, 'No changes to commit');
      }
    } else {
      pushProgress(session, sessionId, 'No changes were made by the agent');
    }

    // Mark as completed
    pushProgress(session, sessionId, 'Task completed successfully!');
    updateStatus(session, sessionId, 'completed');

  } catch (error) {
    session.error = error.message;
    pushProgress(session, sessionId, `Error: ${error.message}`);
    updateStatus(session, sessionId, 'error');
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
// QA Cell Service Endpoints
// ============================================================================

/**
 * Analyze PR and generate test recommendations
 */
async function analyzePRForTests(sessionId, session, token, environment) {
  const { config, parent_session_id } = session;

  try {
    session.status = 'analyzing';
    session.progress.push('Analyzing code changes...');
    broadcastQACellProgress(sessionId, 'Analyzing code changes...');

    // Get parent session to find repository info
    const parentSession = agentSessions.get(parent_session_id);
    if (!parentSession) {
      throw new Error('Parent session not found');
    }

    // Call Claude API to analyze the diff
    const baseUrl = ANTHROPIC_ENDPOINTS[environment] || ANTHROPIC_ENDPOINTS['STAGING'];

    const analysisPrompt = `You are a QA engineer analyzing code changes. Analyze the changes between branch "${config.source_branch}" and "${config.target_branch}".

Based on the following test types requested: ${config.test_types.join(', ')}

Provide a JSON response with:
1. summary: Brief description of the changes
2. impact_areas: Array of affected areas (e.g., "authentication", "api", "database")
3. changed_files: Array of {path, risk_level (high/medium/low), functions_modified, suggested_tests}
4. dependencies: Array of affected dependencies

Respond ONLY with valid JSON.`;

    const response = await axios.post(
      `${baseUrl}/messages`,
      {
        model: 'claude-sonnet-4-5-20250929',
        max_tokens: 4000,
        messages: [{ role: 'user', content: analysisPrompt }]
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

    let analysisResult;
    try {
      const responseText = response.data.content[0]?.text || '{}';
      // Extract JSON from response (handle markdown code blocks)
      const jsonMatch = responseText.match(/```json\n?([\s\S]*?)```/) || [null, responseText];
      analysisResult = JSON.parse(jsonMatch[1] || responseText);
    } catch (e) {
      log(`[QA Cell ${sessionId}] Failed to parse analysis response`);
      analysisResult = {
        summary: 'Analysis completed',
        impact_areas: [],
        changed_files: [],
        dependencies: []
      };
    }

    session.results.pr_analysis = {
      summary: analysisResult.summary || 'Code changes analyzed',
      impact_areas: analysisResult.impact_areas || [],
      changed_files: (analysisResult.changed_files || []).map(f => ({
        path: f.path,
        risk_level: f.risk_level || 'medium',
        lines_added: f.lines_added || 0,
        lines_removed: f.lines_removed || 0,
        functions_modified: f.functions_modified || [],
        suggested_tests: f.suggested_tests || []
      })),
      dependencies: analysisResult.dependencies || [],
      analyzed_at: getTimestamp()
    };

    session.progress.push('PR analysis complete');
    broadcastQACellProgress(sessionId, 'PR analysis complete');

    // Proceed to test generation
    await generateTests(sessionId, session, token, environment);

  } catch (error) {
    session.status = 'failed';
    session.error = error.message;
    session.progress.push(`Analysis failed: ${error.message}`);
    broadcastQACellStatus(sessionId, session);
    log(`[QA Cell ${sessionId}] Analysis error: ${error.message}`);
  }
}

/**
 * Generate tests based on analysis
 */
async function generateTests(sessionId, session, token, environment) {
  try {
    session.status = 'generating';
    session.progress.push('Generating tests...');
    broadcastQACellProgress(sessionId, 'Generating tests...');

    const { config, results } = session;
    const baseUrl = ANTHROPIC_ENDPOINTS[environment] || ANTHROPIC_ENDPOINTS['STAGING'];

    // Build test generation prompt
    const testTypes = config.test_types;
    const framework = config.frameworks?.unit || 'jest';
    const e2eFramework = config.frameworks?.e2e || 'playwright';

    const generationPrompt = `You are a test generation expert. Based on the following PR analysis, generate tests.

PR Analysis:
${JSON.stringify(results.pr_analysis, null, 2)}

Generate the following test types: ${testTypes.join(', ')}
Unit test framework: ${framework}
E2E framework: ${e2eFramework}
Coverage target: ${config.coverage_target}%

For each test, provide a JSON array with:
{
  "id": "unique-id",
  "type": "unit|integration|e2e|manual",
  "name": "test name",
  "description": "what it tests",
  "file_path": "path/to/test.ts",
  "code": "actual test code",
  "covered_functions": ["functionA", "functionB"]
}

For manual tests, include:
{
  "id": "unique-id",
  "type": "manual",
  "title": "Test Case Title",
  "description": "Description",
  "priority": "critical|high|medium|low",
  "preconditions": ["precondition 1"],
  "steps": ["step 1", "step 2"],
  "expected_results": ["result 1"],
  "estimated_time": 10
}

Respond ONLY with a valid JSON array.`;

    const response = await axios.post(
      `${baseUrl}/messages`,
      {
        model: 'claude-sonnet-4-5-20250929',
        max_tokens: 8000,
        messages: [{ role: 'user', content: generationPrompt }]
      },
      {
        headers: {
          'Content-Type': 'application/json',
          'Grazie-Authenticate-JWT': token,
          'anthropic-version': '2023-06-01'
        },
        timeout: 180000
      }
    );

    let tests;
    try {
      const responseText = response.data.content[0]?.text || '[]';
      const jsonMatch = responseText.match(/```json\n?([\s\S]*?)```/) || [null, responseText];
      tests = JSON.parse(jsonMatch[1] || responseText);
    } catch (e) {
      log(`[QA Cell ${sessionId}] Failed to parse test generation response`);
      tests = [];
    }

    // Separate generated tests and manual tests
    const generatedTests = tests.filter(t => t.type !== 'manual').map(t => ({
      id: t.id || uuidv4(),
      type: t.type,
      name: t.name,
      description: t.description || '',
      file_path: t.file_path || '',
      code: t.code || '',
      covered_functions: t.covered_functions || []
    }));

    const manualTests = tests.filter(t => t.type === 'manual').map(t => ({
      id: t.id || uuidv4(),
      title: t.title || t.name,
      description: t.description || '',
      priority: t.priority || 'medium',
      preconditions: t.preconditions || [],
      steps: t.steps || [],
      expected_results: t.expected_results || [],
      estimated_time: t.estimated_time || 5
    }));

    session.results.generated_tests = generatedTests;
    session.results.manual_test_cases = manualTests;
    session.status = 'awaiting_review';
    session.progress.push(`Generated ${generatedTests.length} automated tests and ${manualTests.length} manual test cases`);

    broadcastQACellStatus(sessionId, session);
    log(`[QA Cell ${sessionId}] Tests generated: ${generatedTests.length} automated, ${manualTests.length} manual`);

  } catch (error) {
    session.status = 'failed';
    session.error = error.message;
    session.progress.push(`Test generation failed: ${error.message}`);
    broadcastQACellStatus(sessionId, session);
    log(`[QA Cell ${sessionId}] Generation error: ${error.message}`);
  }
}

/**
 * Execute approved tests
 */
async function executeTests(sessionId, session) {
  try {
    session.status = 'executing';
    session.progress.push('Executing tests...');
    broadcastQACellProgress(sessionId, 'Executing tests...');

    const { approved_tests } = session;
    const startTime = Date.now();

    // Simulate test execution results (in real implementation, this would run actual tests)
    const testResults = [];
    let passed = 0;
    let failed = 0;
    let skipped = 0;

    for (const test of (approved_tests || session.results.generated_tests || [])) {
      // Simulate test result (in production, this would actually run tests)
      const random = Math.random();
      let status;
      if (random > 0.2) {
        status = 'passed';
        passed++;
      } else if (random > 0.1) {
        status = 'failed';
        failed++;
      } else {
        status = 'skipped';
        skipped++;
      }

      testResults.push({
        name: test.name,
        status,
        duration: Math.floor(Math.random() * 1000) + 100,
        error_message: status === 'failed' ? 'Simulated failure for demo' : undefined
      });

      session.progress.push(`Test ${test.name}: ${status}`);
      broadcastQACellProgress(sessionId, `Test ${test.name}: ${status}`);
    }

    const duration = Date.now() - startTime;

    session.results.execution_results = {
      total: testResults.length,
      passed,
      failed,
      skipped,
      duration,
      test_results: testResults,
      flaky_tests: []
    };

    // Simulate coverage
    session.results.coverage = {
      lines: 75 + Math.random() * 20,
      branches: 70 + Math.random() * 20,
      functions: 80 + Math.random() * 15,
      statements: 78 + Math.random() * 17,
      uncovered_lines: [42, 67, 89, 112]
    };

    // Generate gate decision
    const coverageTarget = session.config.coverage_target || 80;
    const avgCoverage = (
      session.results.coverage.lines +
      session.results.coverage.branches +
      session.results.coverage.functions +
      session.results.coverage.statements
    ) / 4;

    let gateStatus = 'pass';
    const issues = [];
    const recommendations = [];

    if (failed > 0) {
      gateStatus = failed > 2 ? 'block' : 'warn';
      issues.push({
        severity: failed > 2 ? 'critical' : 'high',
        message: `${failed} test(s) failed`,
        file: testResults.find(t => t.status === 'failed')?.name
      });
      recommendations.push('Fix failing tests before merging');
    }

    if (avgCoverage < coverageTarget) {
      if (avgCoverage < coverageTarget - 10) {
        gateStatus = 'block';
        issues.push({
          severity: 'critical',
          message: `Coverage ${avgCoverage.toFixed(1)}% is significantly below target ${coverageTarget}%`
        });
      } else {
        if (gateStatus !== 'block') gateStatus = 'warn';
        issues.push({
          severity: 'medium',
          message: `Coverage ${avgCoverage.toFixed(1)}% is below target ${coverageTarget}%`
        });
      }
      recommendations.push('Add tests for uncovered lines');
    }

    session.results.gate_decision = {
      status: gateStatus,
      reasoning: gateStatus === 'pass'
        ? 'All tests passed and coverage target met'
        : `Issues found: ${issues.map(i => i.message).join(', ')}`,
      issues,
      recommendations,
      decided_at: getTimestamp()
    };

    session.status = 'completed';
    session.progress.push('Test execution completed');
    broadcastQACellStatus(sessionId, session);
    log(`[QA Cell ${sessionId}] Execution complete: ${passed} passed, ${failed} failed, gate: ${gateStatus}`);

  } catch (error) {
    session.status = 'failed';
    session.error = error.message;
    session.progress.push(`Execution failed: ${error.message}`);
    broadcastQACellStatus(sessionId, session);
    log(`[QA Cell ${sessionId}] Execution error: ${error.message}`);
  }
}

/**
 * Broadcast QA Cell progress message
 */
function broadcastQACellProgress(sessionId, message) {
  // In a full implementation, this would send WebSocket messages
  log(`[QA Cell ${sessionId}] Progress: ${message}`);
}

/**
 * Broadcast QA Cell status update
 */
function broadcastQACellStatus(sessionId, session) {
  log(`[QA Cell ${sessionId}] Status: ${session.status}`);
}

/**
 * POST /api/qa-cell/start
 * Start a new QA Cell session
 */
app.post('/api/qa-cell/start', (req, res) => {
  try {
    const { session_id, parent_session_id, config } = req.body;

    if (!session_id || !parent_session_id || !config) {
      return res.status(400).json({ error: 'Missing required fields' });
    }

    // Create QA Cell session
    const session = {
      id: session_id,
      parent_session_id,
      config: {
        source_branch: config.source_branch,
        target_branch: config.target_branch,
        test_types: config.test_types || ['unit'],
        coverage_target: config.coverage_target || 80,
        frameworks: config.frameworks || {},
        manual_test_format: config.manual_test_format || 'markdown',
        flake_retry_count: config.flake_retry_count || 1
      },
      status: 'analyzing',
      progress: ['QA Cell session started'],
      results: {
        pr_analysis: null,
        generated_tests: [],
        approved_tests: null,
        execution_results: null,
        coverage: null,
        manual_test_cases: [],
        gate_decision: null
      },
      error: null,
      created_at: getTimestamp()
    };

    qaCellSessions.set(session_id, session);
    log(`[QA Cell] Started session ${session_id} for parent ${parent_session_id}`);

    // Start background analysis (get token from header or config)
    const token = req.headers['grazie-authenticate-jwt'] || req.body.token;
    const environment = config.environment || 'STAGING';

    // Execute analysis in background
    setImmediate(() => {
      analyzePRForTests(session_id, session, token, environment);
    });

    res.json({
      success: true,
      session_id,
      status: 'analyzing'
    });
  } catch (error) {
    log(`[QA Cell Start] Error: ${error.message}`);
    res.status(500).json({ error: error.message });
  }
});

/**
 * GET /api/qa-cell/:id/status
 * Get QA Cell session status
 */
app.get('/api/qa-cell/:id/status', (req, res) => {
  const { id } = req.params;

  const session = qaCellSessions.get(id);
  if (!session) {
    return res.status(404).json({ error: 'QA Cell session not found' });
  }

  res.json({
    session_id: id,
    status: session.status,
    progress: session.progress,
    results: session.results,
    error: session.error,
    created_at: session.created_at,
    timestamp: getTimestamp()
  });
});

/**
 * POST /api/qa-cell/approve-tests
 * Approve generated tests for execution
 */
app.post('/api/qa-cell/approve-tests', (req, res) => {
  try {
    const { session_id, approved_test_ids } = req.body;

    const session = qaCellSessions.get(session_id);
    if (!session) {
      return res.status(404).json({ error: 'QA Cell session not found' });
    }

    if (session.status !== 'awaiting_review') {
      return res.status(400).json({ error: 'Session is not awaiting review' });
    }

    // Filter to only approved tests
    const approvedTests = session.results.generated_tests.filter(
      t => approved_test_ids.includes(t.id)
    );

    session.approved_tests = approvedTests;
    session.progress.push(`${approvedTests.length} tests approved for execution`);

    // Start test execution
    setImmediate(() => {
      executeTests(session_id, session);
    });

    res.json({
      success: true,
      approved_count: approvedTests.length,
      status: 'executing'
    });
  } catch (error) {
    log(`[QA Cell Approve] Error: ${error.message}`);
    res.status(500).json({ error: error.message });
  }
});

/**
 * POST /api/qa-cell/regenerate-test
 * Regenerate a test with feedback
 */
app.post('/api/qa-cell/regenerate-test', async (req, res) => {
  try {
    const { session_id, test_id, feedback } = req.body;

    const session = qaCellSessions.get(session_id);
    if (!session) {
      return res.status(404).json({ error: 'QA Cell session not found' });
    }

    const testIndex = session.results.generated_tests.findIndex(t => t.id === test_id);
    if (testIndex === -1) {
      return res.status(404).json({ error: 'Test not found' });
    }

    const originalTest = session.results.generated_tests[testIndex];
    session.progress.push(`Regenerating test: ${originalTest.name}`);

    // In a full implementation, this would call Claude to regenerate
    // For now, we'll simulate by updating the test
    const regeneratedTest = {
      ...originalTest,
      id: uuidv4(),
      description: `${originalTest.description} (regenerated based on: ${feedback})`,
      code: `// Regenerated based on feedback: ${feedback}\n${originalTest.code}`
    };

    session.results.generated_tests[testIndex] = regeneratedTest;
    session.progress.push(`Test regenerated: ${regeneratedTest.name}`);

    res.json({
      success: true,
      test: regeneratedTest
    });
  } catch (error) {
    log(`[QA Cell Regenerate] Error: ${error.message}`);
    res.status(500).json({ error: error.message });
  }
});

/**
 * POST /api/qa-cell/run-tests
 * Run all approved tests
 */
app.post('/api/qa-cell/run-tests', (req, res) => {
  try {
    const { session_id } = req.body;

    const session = qaCellSessions.get(session_id);
    if (!session) {
      return res.status(404).json({ error: 'QA Cell session not found' });
    }

    session.progress.push('Starting test execution');

    setImmediate(() => {
      executeTests(session_id, session);
    });

    res.json({
      success: true,
      status: 'executing'
    });
  } catch (error) {
    log(`[QA Cell Run] Error: ${error.message}`);
    res.status(500).json({ error: error.message });
  }
});

/**
 * POST /api/qa-cell/rerun-tests
 * Rerun specific tests
 */
app.post('/api/qa-cell/rerun-tests', (req, res) => {
  try {
    const { session_id, test_ids } = req.body;

    const session = qaCellSessions.get(session_id);
    if (!session) {
      return res.status(404).json({ error: 'QA Cell session not found' });
    }

    // Filter tests to rerun
    const testsToRerun = session.results.generated_tests.filter(
      t => test_ids.includes(t.name) || test_ids.includes(t.id)
    );

    session.approved_tests = testsToRerun;
    session.progress.push(`Rerunning ${testsToRerun.length} tests`);

    setImmediate(() => {
      executeTests(session_id, session);
    });

    res.json({
      success: true,
      rerun_count: testsToRerun.length,
      status: 'executing'
    });
  } catch (error) {
    log(`[QA Cell Rerun] Error: ${error.message}`);
    res.status(500).json({ error: error.message });
  }
});

/**
 * POST /api/qa-cell/override-gate
 * Override a quality gate decision
 */
app.post('/api/qa-cell/override-gate', (req, res) => {
  try {
    const { session_id, reason, overridden_at } = req.body;

    const session = qaCellSessions.get(session_id);
    if (!session) {
      return res.status(404).json({ error: 'QA Cell session not found' });
    }

    if (!session.results.gate_decision) {
      return res.status(400).json({ error: 'No gate decision to override' });
    }

    session.results.gate_decision.override_reason = reason;
    session.results.gate_decision.overridden_at = overridden_at || getTimestamp();
    session.progress.push(`Gate decision overridden: ${reason}`);

    log(`[QA Cell ${session_id}] Gate overridden: ${reason}`);

    res.json({
      success: true,
      gate_decision: session.results.gate_decision
    });
  } catch (error) {
    log(`[QA Cell Override] Error: ${error.message}`);
    res.status(500).json({ error: error.message });
  }
});

/**
 * POST /api/qa-cell/cancel
 * Cancel a QA Cell session
 */
app.post('/api/qa-cell/cancel', (req, res) => {
  try {
    const { session_id } = req.body;

    const session = qaCellSessions.get(session_id);
    if (!session) {
      return res.status(404).json({ error: 'QA Cell session not found' });
    }

    session.status = 'cancelled';
    session.progress.push('Session cancelled by user');

    log(`[QA Cell ${session_id}] Cancelled`);

    res.json({
      success: true,
      status: 'cancelled'
    });
  } catch (error) {
    log(`[QA Cell Cancel] Error: ${error.message}`);
    res.status(500).json({ error: error.message });
  }
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
// WebSocket Setup for Real-time Agent Updates
// ============================================================================

// Handle WebSocket upgrade requests
server.on('upgrade', (request, socket, head) => {
  const url = new URL(request.url, `http://${request.headers.host}`);
  const match = url.pathname.match(/^\/api\/agent\/ws\/(.+)$/);

  if (match && PORT === 8001) {
    const sessionId = match[1];
    log(`[WebSocket] Upgrade request for session: ${sessionId}`);

    wss.handleUpgrade(request, socket, head, (ws) => {
      ws.sessionId = sessionId;
      wss.emit('connection', ws, request);
    });
  } else {
    log(`[WebSocket] Rejecting upgrade request: ${url.pathname}`);
    socket.destroy();
  }
});

// Handle WebSocket connections
wss.on('connection', (ws) => {
  const sessionId = ws.sessionId;
  log(`[WebSocket] Client connected for session: ${sessionId}`);

  // Add client to session clients map
  if (!sessionClients.has(sessionId)) {
    sessionClients.set(sessionId, new Set());
  }
  sessionClients.get(sessionId).add(ws);

  // Send current state immediately on connect
  const session = agentSessions.get(sessionId);
  if (session) {
    ws.send(JSON.stringify({
      type: 'status',
      state: {
        status: session.status,
        progress: session.progress || [],
        gitStatus: session.git_status || {
          cloning: false,
          cloned: false,
          branch_created: false,
          committed: false,
          pushed: false,
        },
        files: session.files || [],
        error: session.error,
      }
    }));
  }

  // Handle client messages (if needed in future)
  ws.on('message', (message) => {
    try {
      const data = JSON.parse(message);
      log(`[WebSocket] Received message from ${sessionId}:`, data);
    } catch (e) {
      log(`[WebSocket] Invalid message from ${sessionId}`);
    }
  });

  // Handle client disconnect
  ws.on('close', () => {
    log(`[WebSocket] Client disconnected for session: ${sessionId}`);
    sessionClients.get(sessionId)?.delete(ws);
    if (sessionClients.get(sessionId)?.size === 0) {
      sessionClients.delete(sessionId);
    }
  });

  // Handle errors
  ws.on('error', (error) => {
    log(`[WebSocket] Error for session ${sessionId}: ${error.message}`);
  });
});

/**
 * Broadcast progress message to all clients for a session
 */
function broadcastProgress(sessionId, message) {
  const clients = sessionClients.get(sessionId);
  if (!clients || clients.size === 0) return;

  const payload = JSON.stringify({ type: 'progress', message });
  clients.forEach(ws => {
    if (ws.readyState === 1) { // WebSocket.OPEN
      try {
        ws.send(payload);
      } catch (e) {
        log(`[WebSocket] Failed to send progress to ${sessionId}: ${e.message}`);
      }
    }
  });
}

/**
 * Broadcast status update to all clients for a session
 */
function broadcastStatus(sessionId, state) {
  const clients = sessionClients.get(sessionId);
  if (!clients || clients.size === 0) return;

  const payload = JSON.stringify({ type: 'status', state });
  clients.forEach(ws => {
    if (ws.readyState === 1) { // WebSocket.OPEN
      try {
        ws.send(payload);
      } catch (e) {
        log(`[WebSocket] Failed to send status to ${sessionId}: ${e.message}`);
      }
    }
  });
}

// Make broadcast functions available globally
global.broadcastProgress = broadcastProgress;
global.broadcastStatus = broadcastStatus;

// ============================================================================
// Start Server
// ============================================================================

server.listen(PORT, '0.0.0.0', () => {
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
    log('  WS   /api/agent/ws/:id     - WebSocket for real-time updates');
    log('  --- QA Cell Endpoints ---');
    log('  POST /api/qa-cell/start   - Start QA Cell session');
    log('  GET  /api/qa-cell/:id/status - Get QA Cell status');
    log('  POST /api/qa-cell/approve-tests - Approve tests');
    log('  POST /api/qa-cell/regenerate-test - Regenerate test');
    log('  POST /api/qa-cell/run-tests - Run tests');
    log('  POST /api/qa-cell/rerun-tests - Rerun failed tests');
    log('  POST /api/qa-cell/override-gate - Override gate decision');
    log('  POST /api/qa-cell/cancel  - Cancel QA Cell');
  }
  log('========================================');
});

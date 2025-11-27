#!/usr/bin/env node
const express = require('express');
const os = require('os');

// Create two Express apps - one for each port
const chatApp = express();
const agentApp = express();

chatApp.use(express.json());
agentApp.use(express.json());

// Enable CORS for all routes
const corsMiddleware = (req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.header('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  if (req.method === 'OPTIONS') {
    return res.sendStatus(200);
  }
  next();
};

chatApp.use(corsMiddleware);
agentApp.use(corsMiddleware);

// Get container info
const containerName = process.env.CONTAINER_NAME || 'unknown';
const hostname = os.hostname();

// ===== CHAT SERVICE ENDPOINTS (Port 8000) =====

chatApp.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    service: 'chat',
    container: containerName,
    hostname: hostname,
    timestamp: new Date().toISOString(),
    port: 8000
  });
});

chatApp.post('/chat', (req, res) => {
  const { message, session_id } = req.body;
  res.json({
    response: `Hello! You said: ${message}`,
    session_id: session_id || 'default-session',
    timestamp: new Date().toISOString(),
    container: containerName
  });
});

chatApp.post('/api/chat', (req, res) => {
  const { message, model, token } = req.body;
  res.json({
    response: `Chat API response to: ${message}`,
    model: model || 'default',
    timestamp: new Date().toISOString(),
    container: containerName
  });
});

chatApp.post('/api/models', (req, res) => {
  res.json({
    models: [
      { id: 'claude-sonnet-4-5', name: 'Claude Sonnet 4.5', provider: 'Anthropic' },
      { id: 'gpt-4o', name: 'GPT-4o', provider: 'OpenAI' }
    ],
    timestamp: new Date().toISOString()
  });
});

chatApp.post('/api/validate_token', (req, res) => {
  const { token } = req.body;
  res.json({
    valid: !!token,
    timestamp: new Date().toISOString()
  });
});

// ===== AGENT SERVICE ENDPOINTS (Port 8001) =====

agentApp.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    service: 'agent',
    container: containerName,
    hostname: hostname,
    timestamp: new Date().toISOString(),
    port: 8001
  });
});

agentApp.get('/agent/health', (req, res) => {
  res.json({
    status: 'healthy',
    service: 'agent',
    container: containerName,
    hostname: hostname,
    timestamp: new Date().toISOString(),
    port: 8001
  });
});

agentApp.get('/api/health', (req, res) => {
  res.json({
    status: 'healthy',
    service: 'agent',
    container: containerName,
    hostname: hostname,
    timestamp: new Date().toISOString(),
    port: 8001
  });
});

agentApp.post('/api/agent/start', (req, res) => {
  const { task, model, token } = req.body;
  const sessionId = `session-${Date.now()}`;
  res.json({
    session_id: sessionId,
    status: 'running',
    task: task,
    timestamp: new Date().toISOString()
  });
});

agentApp.post('/api/agent/git-task', (req, res) => {
  const { task, git_repo_url, branch_name } = req.body;
  const sessionId = `git-session-${Date.now()}`;
  res.json({
    session_id: sessionId,
    status: 'running',
    branch_name: branch_name || 'claude-agent-branch',
    timestamp: new Date().toISOString()
  });
});

agentApp.get('/api/agent/status/:session_id', (req, res) => {
  res.json({
    session_id: req.params.session_id,
    status: 'completed',
    progress: ['Task completed successfully'],
    timestamp: new Date().toISOString()
  });
});

agentApp.post('/api/models', (req, res) => {
  res.json({
    models: [
      { id: 'claude-sonnet-4-5', name: 'Claude Sonnet 4.5', provider: 'Anthropic' }
    ],
    timestamp: new Date().toISOString()
  });
});

agentApp.post('/api/validate_token', (req, res) => {
  const { token } = req.body;
  res.json({
    valid: !!token,
    timestamp: new Date().toISOString()
  });
});

// Start Chat Service on port 8000
const chatServer = chatApp.listen(8000, '0.0.0.0', () => {
  console.log(`[${new Date().toISOString()}] Chat Service started on port 8000`);
});

// Start Agent Service on port 8001
const agentServer = agentApp.listen(8001, '0.0.0.0', () => {
  console.log(`[${new Date().toISOString()}] Agent Service started on port 8001`);
});

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('SIGTERM received, shutting down gracefully...');
  chatServer.close(() => console.log('Chat server closed'));
  agentServer.close(() => console.log('Agent server closed'));
});

process.on('SIGINT', () => {
  console.log('SIGINT received, shutting down gracefully...');
  chatServer.close(() => console.log('Chat server closed'));
  agentServer.close(() => console.log('Agent server closed'));
  process.exit(0);
});

console.log(`\n${'='.repeat(50)}`);
console.log('Unified Node.js Service Ready');
console.log(`${'='.repeat(50)}`);
console.log(`Container: ${containerName}`);
console.log(`Hostname: ${hostname}`);
console.log(`Chat Service:  http://localhost:8000/health`);
console.log(`Agent Service: http://localhost:8001/health`);
console.log(`${'='.repeat(50)}\n`);

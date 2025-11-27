const express = require('express');
const app = express();

// Parse JSON bodies
app.use(express.json());

// Enable CORS
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.header('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  if (req.method === 'OPTIONS') {
    return res.sendStatus(200);
  }
  next();
});

// Chat endpoints
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    service: 'chat',
    port: parseInt(process.env.PORT || 8000)
  });
});

app.post('/chat', (req, res) => {
  const message = req.body.message || '';
  res.json({
    response: `Chat service received: ${message}`,
    service: 'chat',
    status: 'success'
  });
});

// Agent endpoints
app.get('/agent/health', (req, res) => {
  res.json({
    status: 'healthy',
    service: 'agent',
    port: parseInt(process.env.PORT || 8001)
  });
});

app.post('/agent/execute', (req, res) => {
  const command = req.body.command || '';
  res.json({
    message: 'Agent execution endpoint',
    command: command,
    status: 'ready',
    claudeCodeAvailable: false,
    service: 'agent'
  });
});

app.get('/agent/status', (req, res) => {
  res.json({
    status: 'running',
    service: 'agent',
    port: parseInt(process.env.PORT || 8001)
  });
});

// IDE endpoints
app.get('/ide/healthz', (req, res) => {
  res.json({
    status: 'healthy',
    service: 'ide',
    codeServerRunning: true
  });
});

app.get('/ide/status', (req, res) => {
  res.json({
    status: 'running',
    service: 'ide',
    port: 8080
  });
});

// Start server
const PORT = process.env.PORT || 8000;
app.listen(PORT, '0.0.0.0', () => {
  console.log(`========================================`);
  console.log(`Unified Service (Node.js) started`);
  console.log(`Listening on port ${PORT}`);
  console.log(`========================================`);
  console.log(`Available endpoints:`);
  console.log(`  GET  /health              - Chat service health`);
  console.log(`  POST /chat                - Chat with Grazie`);
  console.log(`  GET  /agent/health        - Agent service health`);
  console.log(`  POST /agent/execute       - Execute agent command`);
  console.log(`  GET  /agent/status        - Agent status`);
  console.log(`  GET  /ide/healthz         - IDE health check`);
  console.log(`  GET  /ide/status          - IDE status`);
  console.log(`========================================`);
});

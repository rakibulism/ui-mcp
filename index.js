#!/usr/bin/env node
const { spawn } = require('node:child_process');
const path = require('node:path');

const serverPath = path.join(__dirname, 'mcp', 'server.py');
const cliArgs = process.argv.slice(2);

const child = spawn('python', [serverPath, ...cliArgs], {
  stdio: 'inherit',
});

child.on('error', (err) => {
  console.error('Failed to start MCP server:', err.message);
  process.exit(1);
});

child.on('exit', (code, signal) => {
  if (signal) {
    process.exit(1);
    return;
  }
  process.exit(code ?? 0);
});

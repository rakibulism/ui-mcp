#!/usr/bin/env node
const execa = require('execa');
const path = require('path');

const serverPath = path.join(__dirname, 'mcp', 'server.py');

(async () => {
  try {
    const subprocess = execa('python', [serverPath], { stdio: 'inherit' });
    await subprocess;
  } catch (err) {
    console.error('Failed to start MCP server:', err);
    process.exit(1);
  }
})();

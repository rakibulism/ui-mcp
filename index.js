#!/usr/bin/env node
const { spawnSync, spawn } = require('child_process');
const path = require('path');

const serverPath = path.join(__dirname, 'mcp/server.py');
const reqPath = path.join(__dirname, 'mcp/requirements.txt');

// Try installing Python dependencies automatically (pip3 first, then pip)
spawnSync('pip3', ['install', '-r', reqPath], { stdio: 'inherit' });
spawnSync('pip', ['install', '-r', reqPath], { stdio: 'inherit' });

// Try python3 first, fall back to python
function trySpawn(cmd) {
  const proc = spawn(cmd, [serverPath], { stdio: 'inherit' });
  proc.on('error', (err) => {
    if (cmd === 'python3') {
      console.warn(`'${cmd}' not found, retrying with 'python'...`);
      trySpawn('python');
    } else {
      console.error(`Failed to start MCP server: ${err.message}`);
      process.exit(1);
    }
  });
  proc.on('close', (code) => {
    console.log(`MCP server exited with code ${code}`);
  });
}

trySpawn('python3');

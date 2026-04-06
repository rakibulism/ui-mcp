#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import readline from 'node:readline';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT = path.resolve(__dirname, '..');
const DEFAULT_DATA_FILE = path.join(ROOT, 'shots-data.js');

const TAG_SEEDS = [
  'dashboard', 'admin', 'crm', 'finance', 'fintech', 'ecommerce', 'seo', 'hr',
  'task', 'portfolio', 'investor', 'analytics', 'education', 'ev', 'lms', 'sales'
];

function parseArgs(argv = process.argv.slice(2)) {
  const args = {};
  for (let i = 0; i < argv.length; i += 1) {
    const token = argv[i];
    if (token === '--data') {
      args.data = argv[i + 1];
      i += 1;
    }
  }
  return args;
}

function resolveDataFile(dataArg) {
  const selected = dataArg || process.env.SHOTS_DATA_PATH;
  if (selected) {
    const resolved = path.resolve(selected);
    if (!fs.existsSync(resolved)) {
      throw new Error(`shots-data.js not found at: ${resolved}. Please provide --data /path/to/shots-data.js or set SHOTS_DATA_PATH.`);
    }
    return resolved;
  }

  if (fs.existsSync(DEFAULT_DATA_FILE)) return DEFAULT_DATA_FILE;

  throw new Error('shots-data.js is required but was not found. Please provide --data /path/to/shots-data.js or set SHOTS_DATA_PATH.');
}

function loadData(dataFile) {
  const raw = fs.readFileSync(dataFile, 'utf8').trim();
  const prefix = 'window.SHOTS_DATA = ';
  if (!raw.startsWith(prefix) || !raw.endsWith(';')) throw new Error(`${dataFile} format invalid`);
  return JSON.parse(raw.slice(prefix.length, -1));
}

let DATA;
try {
  const args = parseArgs();
  const dataFile = resolveDataFile(args.data);
  DATA = loadData(dataFile);
} catch (err) {
  console.error(`Failed to load shots data: ${err.message}`);
  process.exit(1);
}

const jsonResponse = (id, result, error = null) =>
  error ? { jsonrpc: '2.0', id, error } : { jsonrpc: '2.0', id, result };

const findProject = (projectPath) => DATA.projects.find((p) => p.path === projectPath);
const findImage = (imagePath) => DATA.images.find((i) => i.path === imagePath);
const toAbs = (p, baseUrl) => (baseUrl ? `${baseUrl.replace(/\/$/, '')}/${p.replace(/^\//, '')}` : p);
const tagsForText = (text) => TAG_SEEDS.filter((t) => String(text).toLowerCase().includes(t));
const tokenize = (text) => new Set(String(text).toLowerCase().split(/[^a-z0-9]+/).filter((s) => s.length > 2));
const scoreSimilarity = (a, b) => [...a].filter((x) => b.has(x)).length;

function toolList() {
  return {
    tools: [
      { name: 'get_gallery_stats', description: 'Return totals and category summary for the gallery.', inputSchema: { type: 'object', properties: {}, additionalProperties: false } },
      { name: 'list_projects', description: 'List projects with optional category filter and pagination.', inputSchema: { type: 'object', properties: { category: { type: 'string' }, offset: { type: 'integer', minimum: 0 }, limit: { type: 'integer', minimum: 1, maximum: 500 } }, additionalProperties: false } },
      { name: 'get_project_images', description: 'Return image list for a specific project path.', inputSchema: { type: 'object', properties: { project_path: { type: 'string' } }, required: ['project_path'], additionalProperties: false } },
      { name: 'search_images', description: 'Search images by text query.', inputSchema: { type: 'object', properties: { query: { type: 'string' }, category: { type: 'string' }, limit: { type: 'integer', minimum: 1, maximum: 500 } }, required: ['query'], additionalProperties: false } },
      { name: 'prepare_video_payload', description: 'Return project image URLs for video workflows.', inputSchema: { type: 'object', properties: { project_path: { type: 'string' }, base_url: { type: 'string' } }, required: ['project_path'], additionalProperties: false } },
      { name: 'list_tags', description: 'Return supported design tags used by search/filter experiences.', inputSchema: { type: 'object', properties: {}, additionalProperties: false } },
      { name: 'get_similar_images', description: 'Find visually related images using keyword overlap similarity.', inputSchema: { type: 'object', properties: { image_path: { type: 'string' }, limit: { type: 'integer', minimum: 1, maximum: 50 } }, required: ['image_path'], additionalProperties: false } },
      { name: 'create_video_sequence', description: 'Create a sequence payload with ordered project images for video editors.', inputSchema: { type: 'object', properties: { project_path: { type: 'string' }, max_images: { type: 'integer', minimum: 1, maximum: 50 }, base_url: { type: 'string' } }, required: ['project_path'], additionalProperties: false } },
    ]
  };
}

function toolCall(name, args = {}) {
  let payload;
  if (name === 'get_gallery_stats') {
    payload = { totals: DATA.totals, summary: DATA.summary };
  } else if (name === 'list_projects') {
    const { category, offset = 0, limit = 100 } = args;
    let items = DATA.projects;
    if (category) items = items.filter((p) => p.category === category);
    payload = { count: items.length, items: items.slice(offset, offset + limit) };
  } else if (name === 'get_project_images') {
    const project = findProject(args.project_path);
    if (!project) throw new Error('Project not found');
    payload = { project: { path: project.path, name: project.name, category: project.category, count: project.count }, images: project.images };
  } else if (name === 'search_images') {
    const q = String(args.query || '').trim().toLowerCase();
    const { category, limit = 100 } = args;
    const items = [];
    for (const img of DATA.images) {
      if (category && img.category !== category) continue;
      const hay = `${img.name} ${img.path} ${img.projectPath} ${img.projectName} ${img.category}`.toLowerCase();
      if (hay.includes(q)) items.push({ ...img, tags: tagsForText(hay) });
      if (items.length >= limit) break;
    }
    payload = { count: items.length, items };
  } else if (name === 'prepare_video_payload') {
    const project = findProject(args.project_path);
    if (!project) throw new Error('Project not found');
    payload = {
      project: { path: project.path, name: project.name, category: project.category, count: project.count },
      image_urls: project.images.map((img) => toAbs(img, args.base_url)),
      reecap_url: 'https://reecap.vercel.app/'
    };
  } else if (name === 'list_tags') {
    payload = { count: TAG_SEEDS.length, tags: TAG_SEEDS };
  } else if (name === 'get_similar_images') {
    const target = findImage(args.image_path);
    if (!target) throw new Error('Image not found');
    const limit = Number(args.limit || 12);
    const tkn = tokenize(`${target.name} ${target.projectPath} ${target.category}`);
    const scored = DATA.images
      .filter((img) => img.path !== target.path)
      .map((img) => ({ img, score: scoreSimilarity(tkn, tokenize(`${img.name} ${img.projectPath} ${img.category}`)) }))
      .filter((x) => x.score > 0)
      .sort((a, b) => b.score - a.score || a.img.path.localeCompare(b.img.path))
      .slice(0, limit)
      .map((x) => x.img);
    payload = { source: target, count: scored.length, items: scored };
  } else if (name === 'create_video_sequence') {
    const project = findProject(args.project_path);
    if (!project) throw new Error('Project not found');
    const max = Number(args.max_images || 12);
    const frames = project.images.slice(0, max).map((image, i) => ({ index: i + 1, image_url: toAbs(image, args.base_url), duration_ms: 1500 }));
    payload = {
      project: { path: project.path, name: project.name, category: project.category, count: project.count },
      sequence: frames,
      total_duration_ms: frames.length * 1500,
      suggested_format: '1080x1350'
    };
  } else {
    throw new Error(`Unknown tool: ${name}`);
  }

  return { content: [{ type: 'text', text: JSON.stringify(payload, null, 2) }], structuredContent: payload };
}

function handle(req) {
  const { method, id, params = {} } = req;
  if (method === 'initialize') {
    return jsonResponse(id, { protocolVersion: '2024-11-05', serverInfo: { name: 'social-shots-mcp-js', version: '0.1.0' }, capabilities: { tools: {} } });
  }
  if (method === 'notifications/initialized') return null;
  if (method === 'ping') return jsonResponse(id, { ok: true });
  if (method === 'tools/list') return jsonResponse(id, toolList());
  if (method === 'tools/call') {
    try { return jsonResponse(id, toolCall(params.name, params.arguments || {})); }
    catch (err) { return jsonResponse(id, null, { code: -32000, message: err.message }); }
  }
  return jsonResponse(id, null, { code: -32601, message: `Method not found: ${method}` });
}

const rl = readline.createInterface({ input: process.stdin, crlfDelay: Infinity });
rl.on('line', (line) => {
  const trimmed = line.trim();
  if (!trimmed) return;
  let resp;
  try {
    const req = JSON.parse(trimmed);
    resp = handle(req);
  } catch (err) {
    resp = jsonResponse(null, null, { code: -32700, message: `Parse error: ${err.message}` });
  }
  if (resp) process.stdout.write(`${JSON.stringify(resp)}\n`);
});

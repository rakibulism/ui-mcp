# Social Shots MCP Server

This folder contains MCP servers for the Social Shots dataset.

## Available server runtimes

- `server.mjs` — Node.js stdio MCP server (recommended for npm distribution).
- `server.py` — Python stdio MCP server.

## Tools exposed

1. `get_gallery_stats`
2. `list_projects`
3. `get_project_images`
4. `search_images`
5. `prepare_video_payload`
6. `list_tags`
7. `get_similar_images`
8. `create_video_sequence`

## Install via npm (internet users)

After publishing to npm, users can run:

```bash
npx social-shots-mcp
```

or install globally:

```bash
npm i -g social-shots-mcp
social-shots-mcp
```

## Run locally from repo

Node server:

```bash
node mcp/server.mjs
```

Python server:

```bash
python mcp/server.py
```

## Example MCP client config (Node)

```json
{
  "mcpServers": {
    "social-shots": {
      "command": "npx",
      "args": ["social-shots-mcp"]
    }
  }
}
```

## Notes

- `prepare_video_payload` can return relative paths, or absolute URLs when `base_url` is provided.
- `create_video_sequence` provides frame durations and suggested social format metadata.
- `reecap_url` is included for quick handoff to Reecap workflows.

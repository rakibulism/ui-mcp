# Social Shots MCP Server

This folder contains a minimal MCP server for the Social Shots dataset.

## File

- `server.py` — stdio MCP server exposing tools powered by `../shots-data.js`.

## Tools exposed

1. `get_gallery_stats`
2. `list_projects`
3. `get_project_images`
4. `search_images`
5. `prepare_video_payload`
6. `list_tags`
7. `get_similar_images`
8. `create_video_sequence`

## Run locally

```bash
python mcp/server.py
```

Then send JSON-RPC lines via stdin (MCP stdio transport).

## Example MCP client config (generic)

```json
{
  "mcpServers": {
    "social-shots": {
      "command": "python",
      "args": ["/workspace/social-shots/mcp/server.py"]
    }
  }
}
```

## Notes

- `prepare_video_payload` can return relative paths, or absolute URLs when `base_url` is provided.
- `reecap_url` is included in the payload for quick video workflow handoff.
- `create_video_sequence` provides frame durations and suggested social format metadata.

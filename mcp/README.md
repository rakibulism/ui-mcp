# Social Shots MCP Server

This project includes MCP servers and an npm CLI wrapper.

## Main user path (npm package)

After publishing to npm, users can install and run:

```bash
npm install -g social-shots-mcp
social-shots --data /path/to/shots-data.js
```

This command starts `mcp/server.py`.

Or use an environment variable:

```bash
SHOTS_DATA_PATH=/path/to/shots-data.js social-shots
```

If no data file is found, the server exits with a clear guidance message.

## Tools exposed

1. `get_gallery_stats`
2. `list_projects`
3. `get_project_images`
4. `search_images`
5. `prepare_video_payload`
6. `list_tags`
7. `get_similar_images`
8. `create_video_sequence`

## Local development

Run Python server directly:

```bash
python mcp/server.py --data /path/to/shots-data.js
```

Run Node server directly (optional runtime):

```bash
node mcp/server.mjs --data /path/to/shots-data.js
```

## Example MCP client config

```json
{
  "mcpServers": {
    "social-shots": {
      "command": "social-shots"
    }
  }
}
```

## Publish steps

```bash
npm login
npm publish --access public
```

## Notes

- Ensure Python 3.10+ is available on systems running `social-shots`.
- `prepare_video_payload` can return relative paths, or absolute URLs when `base_url` is provided.
- `create_video_sequence` provides frame durations and suggested social format metadata.

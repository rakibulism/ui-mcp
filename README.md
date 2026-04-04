# Social Shots MCP

A curated collection of UI/UX design shot assets by **Rakibul**, published as an **npm package** that ships an MCP (Model Context Protocol) server for AI-powered design workflows.

[![npm version](https://img.shields.io/npm/v/social-shots-mcp)](https://www.npmjs.com/package/social-shots-mcp)
[![npm downloads](https://img.shields.io/npm/dm/social-shots-mcp)](https://www.npmjs.com/package/social-shots-mcp)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

---

## Quick Start

### Install via npm

```bash
npm install -g social-shots-mcp
```

### Run the MCP Server

```bash
social-shots
```

This will automatically:
1. Install any required Python dependencies (`pip3` / `pip`)
2. Start the MCP server via stdio transport

> **Requires Python 3** to be installed on your system.

---

## What's Inside

A gallery of **51 projects** and **270 design images** covering:

- **Dribbble shots** (single-shot project folders)
- **Instagram carousel shots** (1/1, 1/2, and 1/3 carousel formats)

---

## MCP Tools

Once running, the MCP server exposes the following tools to AI assistants (e.g. Claude, Cursor, Copilot):

| Tool | Description |
|---|---|
| `get_gallery_stats` | Returns totals and category summary |
| `list_projects` | Lists projects with optional category filter and pagination |
| `get_project_images` | Returns all images for a specific project |
| `search_images` | Search images by text query |
| `prepare_video_payload` | Returns project image URLs for video workflows |
| `get_similar_images` | Finds visually related images via keyword similarity |
| `create_video_sequence` | Creates an ordered image sequence for video editors |
| `list_tags` | Returns supported design tags used for filtering |

---

## Connect to Claude Desktop (or any MCP client)

Add this to your MCP client config:

```json
{
  "mcpServers": {
    "social-shots": {
      "command": "social-shots"
    }
  }
}
```

For Claude Desktop, edit `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS).

---

## Manual Setup (without npm)

If you prefer to run the server directly:

```bash
git clone https://github.com/rakibulism/social-shots.git
cd social-shots
pip3 install -r mcp/requirements.txt
python3 mcp/server.py
```

---

## Repository Structure (Full Clone)

The GitHub repo contains the full asset library:

```text
.
├── Dribbble Shot/                  # Single-shot projects
├── Instagram Carousel Saas Shot/   # Carousel shot projects
├── mcp/
│   ├── server.py                   # Python MCP server (stdio)
│   ├── server.mjs                  # JS variant
│   ├── requirements.txt            # Python dependencies
│   └── README.md
├── index.html                      # Public gallery explorer
├── project.html                    # Per-project detail page
├── shots-data.js                   # Generated gallery dataset
├── styles.css                      # Shared gallery styles
├── viewer.html                     # Dedicated image viewer
├── index.js                        # CLI entry point
└── README.md
```

---

## Public Gallery

Browse the full design gallery locally:

1. Clone the repo and open `index.html` in a browser (or serve with any static file server).
2. Use **Project view** to browse assets by project.
3. Click a project card to see details and all images.
4. Click any image to open the viewer with navigation, download, and **Make video** shortcut to [Reecap](https://reecap.vercel.app/).

---

## License

This repository is distributed under the terms of the [LICENSE](./LICENSE) file.

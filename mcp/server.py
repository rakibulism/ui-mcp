#!/usr/bin/env python3
"""Social Shots MCP server (stdio transport).

Minimal MCP-compatible server exposing gallery tools powered by shots-data.js.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "shots-data.js"


def load_data() -> dict[str, Any]:
    raw = DATA_FILE.read_text(encoding="utf-8").strip()
    prefix = "window.SHOTS_DATA = "
    if not raw.startswith(prefix) or not raw.endswith(";"):
        raise RuntimeError("shots-data.js is not in expected format")
    return json.loads(raw[len(prefix) : -1])


DATA = load_data()


def _json_response(id_value: Any, result: Any = None, error: Any = None) -> dict[str, Any]:
    base = {"jsonrpc": "2.0", "id": id_value}
    if error is not None:
        base["error"] = error
    else:
        base["result"] = result
    return base


def _tool_list() -> dict[str, Any]:
    return {
        "tools": [
            {
                "name": "get_gallery_stats",
                "description": "Return totals and category summary for the Social Shots gallery.",
                "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
            },
            {
                "name": "list_projects",
                "description": "List projects with optional category filter and pagination.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "category": {"type": "string"},
                        "offset": {"type": "integer", "minimum": 0},
                        "limit": {"type": "integer", "minimum": 1, "maximum": 500},
                    },
                    "additionalProperties": False,
                },
            },
            {
                "name": "get_project_images",
                "description": "Return image list for a specific project path.",
                "inputSchema": {
                    "type": "object",
                    "properties": {"project_path": {"type": "string"}},
                    "required": ["project_path"],
                    "additionalProperties": False,
                },
            },
            {
                "name": "search_images",
                "description": "Search images by text query across image name/path/project/category.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "category": {"type": "string"},
                        "limit": {"type": "integer", "minimum": 1, "maximum": 500},
                    },
                    "required": ["query"],
                    "additionalProperties": False,
                },
            },
            {
                "name": "prepare_video_payload",
                "description": "Return project image URLs and metadata for video workflows (e.g., Reecap import).",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "project_path": {"type": "string"},
                        "base_url": {"type": "string"},
                    },
                    "required": ["project_path"],
                    "additionalProperties": False,
                },
            },
        ]
    }


def _find_project(path: str) -> dict[str, Any] | None:
    return next((p for p in DATA["projects"] if p["path"] == path), None)


def _to_abs(path: str, base_url: str | None) -> str:
    if not base_url:
        return path
    return base_url.rstrip("/") + "/" + path.lstrip("/")


def _tool_call(name: str, args: dict[str, Any]) -> dict[str, Any]:
    if name == "get_gallery_stats":
        payload = {
            "totals": DATA["totals"],
            "summary": DATA["summary"],
        }
    elif name == "list_projects":
        category = args.get("category")
        offset = int(args.get("offset", 0))
        limit = int(args.get("limit", 100))
        items = DATA["projects"]
        if category:
            items = [p for p in items if p.get("category") == category]
        payload = {
            "count": len(items),
            "items": items[offset : offset + limit],
        }
    elif name == "get_project_images":
        project_path = args.get("project_path")
        project = _find_project(project_path)
        if not project:
            raise ValueError(f"Project not found: {project_path}")
        payload = {
            "project": {
                "path": project["path"],
                "name": project["name"],
                "category": project["category"],
                "count": project["count"],
            },
            "images": project["images"],
        }
    elif name == "search_images":
        query = str(args.get("query", "")).strip().lower()
        category = args.get("category")
        limit = int(args.get("limit", 100))
        items = []
        for img in DATA["images"]:
            if category and img.get("category") != category:
                continue
            haystack = " ".join([
                img.get("name", ""),
                img.get("path", ""),
                img.get("projectPath", ""),
                img.get("projectName", ""),
                img.get("category", ""),
            ]).lower()
            if query in haystack:
                items.append(img)
            if len(items) >= limit:
                break
        payload = {"count": len(items), "items": items}
    elif name == "prepare_video_payload":
        project_path = args.get("project_path")
        base_url = args.get("base_url")
        project = _find_project(project_path)
        if not project:
            raise ValueError(f"Project not found: {project_path}")
        urls = [_to_abs(path, base_url) for path in project["images"]]
        payload = {
            "project": {
                "path": project["path"],
                "name": project["name"],
                "category": project["category"],
                "count": project["count"],
            },
            "image_urls": urls,
            "reecap_url": "https://reecap.vercel.app/",
        }
    else:
        raise ValueError(f"Unknown tool: {name}")

    return {
        "content": [{"type": "text", "text": json.dumps(payload, ensure_ascii=False, indent=2)}],
        "structuredContent": payload,
    }


def handle(req: dict[str, Any]) -> dict[str, Any] | None:
    method = req.get("method")
    id_value = req.get("id")
    params = req.get("params", {})

    if method == "initialize":
        return _json_response(
            id_value,
            {
                "protocolVersion": "2024-11-05",
                "serverInfo": {"name": "social-shots-mcp", "version": "0.1.0"},
                "capabilities": {"tools": {}},
            },
        )

    if method == "notifications/initialized":
        return None

    if method == "ping":
        return _json_response(id_value, {"ok": True})

    if method == "tools/list":
        return _json_response(id_value, _tool_list())

    if method == "tools/call":
        try:
            result = _tool_call(params.get("name", ""), params.get("arguments", {}))
            return _json_response(id_value, result)
        except Exception as exc:  # noqa: BLE001
            return _json_response(
                id_value,
                error={"code": -32000, "message": str(exc)},
            )

    return _json_response(
        id_value,
        error={"code": -32601, "message": f"Method not found: {method}"},
    )


def main() -> int:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            resp = handle(req)
        except Exception as exc:  # noqa: BLE001
            resp = _json_response(None, error={"code": -32700, "message": f"Parse error: {exc}"})

        if resp is not None:
            sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
            sys.stdout.flush()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

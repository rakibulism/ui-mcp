#!/usr/bin/env python3
"""Social Shots MCP server (stdio transport)."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_FILE = ROOT / "shots-data.js"
TAG_SEEDS = [
    "dashboard", "admin", "crm", "finance", "fintech", "ecommerce", "seo", "hr",
    "task", "portfolio", "investor", "analytics", "education", "ev", "lms", "sales",
]

DATA: dict[str, Any] = {}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Social Shots MCP server.")
    parser.add_argument(
        "--data",
        type=Path,
        help="Path to shots-data.js (can also be provided via SHOTS_DATA_PATH).",
    )
    return parser.parse_args(argv)


def resolve_data_file(data_arg: Path | None) -> Path:
    selected = data_arg or os.getenv("SHOTS_DATA_PATH")

    if selected:
        path = Path(selected).expanduser().resolve()
        if not path.exists():
            raise RuntimeError(
                f"shots-data.js not found at: {path}. "
                "Please provide --data /path/to/shots-data.js or set SHOTS_DATA_PATH."
            )
        return path

    if DEFAULT_DATA_FILE.exists():
        return DEFAULT_DATA_FILE

    raise RuntimeError(
        "shots-data.js is required but was not found. "
        "Please provide --data /path/to/shots-data.js or set SHOTS_DATA_PATH."
    )


def load_data(data_file: Path) -> dict[str, Any]:
    raw = data_file.read_text(encoding="utf-8").strip()
    prefix = "window.SHOTS_DATA = "
    if not raw.startswith(prefix) or not raw.endswith(";"):
        raise RuntimeError(f"{data_file} is not in expected format")
    return json.loads(raw[len(prefix) : -1])


def _json_response(id_value: Any, result: Any = None, error: Any = None) -> dict[str, Any]:
    base = {"jsonrpc": "2.0", "id": id_value}
    if error is not None:
        base["error"] = error
    else:
        base["result"] = result
    return base


def _tags_for_text(text: str) -> list[str]:
    text = text.lower()
    return [t for t in TAG_SEEDS if t in text]


def _score_similarity(base: set[str], cand: set[str]) -> int:
    return len(base.intersection(cand))


def _tool_list() -> dict[str, Any]:
    return {
        "tools": [
            {"name": "get_gallery_stats", "description": "Return totals and category summary for the gallery.", "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False}},
            {"name": "list_projects", "description": "List projects with optional category filter and pagination.", "inputSchema": {"type": "object", "properties": {"category": {"type": "string"}, "offset": {"type": "integer", "minimum": 0}, "limit": {"type": "integer", "minimum": 1, "maximum": 500}}, "additionalProperties": False}},
            {"name": "get_project_images", "description": "Return image list for a specific project path.", "inputSchema": {"type": "object", "properties": {"project_path": {"type": "string"}}, "required": ["project_path"], "additionalProperties": False}},
            {"name": "search_images", "description": "Search images by text query.", "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}, "category": {"type": "string"}, "limit": {"type": "integer", "minimum": 1, "maximum": 500}}, "required": ["query"], "additionalProperties": False}},
            {"name": "prepare_video_payload", "description": "Return project image URLs for video workflows.", "inputSchema": {"type": "object", "properties": {"project_path": {"type": "string"}, "base_url": {"type": "string"}}, "required": ["project_path"], "additionalProperties": False}},
            {"name": "list_tags", "description": "Return supported design tags used by search/filter experiences.", "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False}},
            {"name": "get_similar_images", "description": "Find visually related images using keyword overlap similarity.", "inputSchema": {"type": "object", "properties": {"image_path": {"type": "string"}, "limit": {"type": "integer", "minimum": 1, "maximum": 50}}, "required": ["image_path"], "additionalProperties": False}},
            {"name": "create_video_sequence", "description": "Create a sequence payload with ordered project images for video editors.", "inputSchema": {"type": "object", "properties": {"project_path": {"type": "string"}, "max_images": {"type": "integer", "minimum": 1, "maximum": 50}, "base_url": {"type": "string"}}, "required": ["project_path"], "additionalProperties": False}},
        ]
    }


def _find_project(path: str) -> dict[str, Any] | None:
    return next((p for p in DATA["projects"] if p["path"] == path), None)


def _find_image(path: str) -> dict[str, Any] | None:
    return next((i for i in DATA["images"] if i["path"] == path), None)


def _to_abs(path: str, base_url: str | None) -> str:
    return path if not base_url else base_url.rstrip("/") + "/" + path.lstrip("/")


def _tokenize(text: str) -> set[str]:
    return {t for t in re.split(r"[^a-z0-9]+", text.lower()) if len(t) > 2}


def _tool_call(name: str, args: dict[str, Any]) -> dict[str, Any]:
    if name == "get_gallery_stats":
        payload = {"totals": DATA["totals"], "summary": DATA["summary"]}
    elif name == "list_projects":
        category = args.get("category")
        offset = int(args.get("offset", 0))
        limit = int(args.get("limit", 100))
        items = DATA["projects"]
        if category:
            items = [p for p in items if p.get("category") == category]
        payload = {"count": len(items), "items": items[offset : offset + limit]}
    elif name == "get_project_images":
        project = _find_project(args.get("project_path"))
        if not project:
            raise ValueError("Project not found")
        payload = {"project": {k: project[k] for k in ["path", "name", "category", "count"]}, "images": project["images"]}
    elif name == "search_images":
        query = str(args.get("query", "")).strip().lower()
        category = args.get("category")
        limit = int(args.get("limit", 100))
        items = []
        for img in DATA["images"]:
            if category and img.get("category") != category:
                continue
            haystack = f"{img.get('name','')} {img.get('path','')} {img.get('projectPath','')} {img.get('projectName','')} {img.get('category','')}".lower()
            if query in haystack:
                row = dict(img)
                row["tags"] = _tags_for_text(haystack)
                items.append(row)
            if len(items) >= limit:
                break
        payload = {"count": len(items), "items": items}
    elif name == "prepare_video_payload":
        project = _find_project(args.get("project_path"))
        if not project:
            raise ValueError("Project not found")
        base_url = args.get("base_url")
        payload = {
            "project": {k: project[k] for k in ["path", "name", "category", "count"]},
            "image_urls": [_to_abs(path, base_url) for path in project["images"]],
            "reecap_url": "https://reecap.vercel.app/",
        }
    elif name == "list_tags":
        payload = {"count": len(TAG_SEEDS), "tags": TAG_SEEDS}
    elif name == "get_similar_images":
        target = _find_image(args.get("image_path"))
        if not target:
            raise ValueError("Image not found")
        limit = int(args.get("limit", 12))
        target_tokens = _tokenize(f"{target['name']} {target['projectPath']} {target['category']}")
        scored = []
        for img in DATA["images"]:
            if img["path"] == target["path"]:
                continue
            tokens = _tokenize(f"{img['name']} {img['projectPath']} {img['category']}")
            score = _score_similarity(target_tokens, tokens)
            if score > 0:
                scored.append((score, img))
        scored.sort(key=lambda x: (-x[0], x[1]["path"]))
        payload = {"source": target, "count": min(limit, len(scored)), "items": [img for _, img in scored[:limit]]}
    elif name == "create_video_sequence":
        project = _find_project(args.get("project_path"))
        if not project:
            raise ValueError("Project not found")
        max_images = int(args.get("max_images", 12))
        base_url = args.get("base_url")
        frames = [_to_abs(path, base_url) for path in project["images"][:max_images]]
        payload = {
            "project": {k: project[k] for k in ["path", "name", "category", "count"]},
            "sequence": [{"index": i + 1, "image_url": u, "duration_ms": 1500} for i, u in enumerate(frames)],
            "total_duration_ms": len(frames) * 1500,
            "suggested_format": "1080x1350",
        }
    else:
        raise ValueError(f"Unknown tool: {name}")

    return {"content": [{"type": "text", "text": json.dumps(payload, ensure_ascii=False, indent=2)}], "structuredContent": payload}


def handle(req: dict[str, Any]) -> dict[str, Any] | None:
    method = req.get("method")
    id_value = req.get("id")
    params = req.get("params", {})

    if method == "initialize":
        return _json_response(id_value, {"protocolVersion": "2024-11-05", "serverInfo": {"name": "social-shots-mcp", "version": "0.2.0"}, "capabilities": {"tools": {}}})
    if method == "notifications/initialized":
        return None
    if method == "ping":
        return _json_response(id_value, {"ok": True})
    if method == "tools/list":
        return _json_response(id_value, _tool_list())
    if method == "tools/call":
        try:
            return _json_response(id_value, _tool_call(params.get("name", ""), params.get("arguments", {})))
        except Exception as exc:  # noqa: BLE001
            return _json_response(id_value, error={"code": -32000, "message": str(exc)})
    return _json_response(id_value, error={"code": -32601, "message": f"Method not found: {method}"})


def main(argv: list[str] | None = None) -> int:
    global DATA

    args = parse_args(argv)
    try:
        data_file = resolve_data_file(args.data)
        DATA = load_data(data_file)
    except Exception as exc:  # noqa: BLE001
        print(f"Failed to load shots data: {exc}", file=sys.stderr)
        return 1

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

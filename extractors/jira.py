"""
Jira extractor stub.

Production shape: JQL search (or webhook) → Ticket nodes and TRACKS edges to
datasets, pipelines, reports, and docs via issue links / custom fields.
This stub reads a mocked search payload — no live Atlassian tenant required.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXTRACT = ROOT / "fixtures" / "jira_search.json"


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def extract(path: Path | None = None) -> dict[str, Any]:
    """Read Jira search-shaped JSON and emit Ticket + TRACKS graph fragments."""
    source = path or DEFAULT_EXTRACT
    raw = json.loads(source.read_text())
    as_of = raw.get("as_of", "1970-01-01")
    browse_base = raw.get("browse_base_url", "https://example.atlassian.net/browse").rstrip("/")

    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []

    for issue in raw.get("issues", []):
        key = issue["key"]
        fields = issue.get("fields") or {}
        issue_type = (fields.get("issuetype") or {}).get("name", "Task")
        status = (fields.get("status") or {}).get("name", "Open")
        priority = (fields.get("priority") or {}).get("name")
        summary = fields.get("summary")

        nodes.append(
            {
                "label": "Ticket",
                "id": key,
                "properties": {
                    "type": issue_type,
                    "status": status,
                    "priority": priority,
                    "summary": summary,
                    "url": f"{browse_base}/{key}",
                },
            }
        )

        for link in fields.get("customfield_asset_links") or []:
            target_id = link["id"]
            edges.append(
                {
                    "type": "TRACKS",
                    "from": key,
                    "to": target_id,
                    "properties": {
                        "source": "jira_search",
                        "as_of": as_of,
                        "confidence": 1.0,
                        "extractor_version": "jira-stub-v0",
                        "target_type": link.get("type"),
                    },
                }
            )

    return {
        "extractor": "jira",
        "source_file": _rel(source),
        "as_of": as_of,
        "nodes": nodes,
        "edges": edges,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Emit Ticket/TRACKS edges from mocked Jira search extracts")
    parser.add_argument("--input", type=Path, default=DEFAULT_EXTRACT)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    print(json.dumps(extract(args.input), indent=2 if args.pretty else None))


if __name__ == "__main__":
    main()

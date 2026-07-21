"""
Snowflake extractor stub.

Production shape: query ACCOUNT_USAGE / INFORMATION_SCHEMA, then emit Dataset
nodes and DERIVES_FROM edges. This stub reads mocked extracts so the pipeline
is demonstrable without live Snowflake credentials.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXTRACT = ROOT / "fixtures" / "snowflake_information_schema.json"


def fq_name(account: str, database: str, schema: str, name: str) -> str:
    return ".".join(part.lower() for part in (account, database, schema, name))


def extract(path: Path | None = None) -> dict[str, Any]:
    """Read INFORMATION_SCHEMA-shaped JSON and emit graph fragments."""
    source = path or DEFAULT_EXTRACT
    raw = json.loads(source.read_text())
    account = raw["account"].lower()
    as_of = raw.get("as_of", "1970-01-01")

    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []

    for row in raw.get("tables", []):
        dataset_id = fq_name(account, row["table_catalog"], row["table_schema"], row["table_name"])
        nodes.append(
            {
                "label": "Dataset",
                "id": dataset_id,
                "properties": {
                    "fq_name": dataset_id,
                    "object_type": row.get("table_type", "BASE TABLE").lower().replace(" ", "_"),
                    "layer": row.get("layer"),
                    "pii": bool(row.get("pii", False)),
                },
            }
        )

    for dep in raw.get("object_dependencies", []):
        referencing = fq_name(
            account,
            dep["referencing_database"],
            dep["referencing_schema"],
            dep["referencing_object_name"],
        )
        referenced = fq_name(
            account,
            dep["referenced_database"],
            dep["referenced_schema"],
            dep["referenced_object_name"],
        )
        edges.append(
            {
                "type": "DERIVES_FROM",
                "from": referencing,
                "to": referenced,
                "properties": {
                    "source": "snowflake_information_schema",
                    "as_of": as_of,
                    "confidence": 1.0,
                    "extractor_version": "snowflake-stub-v0",
                    "dependency_type": dep.get("dependency_type"),
                },
            }
        )

    return {
        "extractor": "snowflake",
        "source_file": str(source.relative_to(ROOT)) if source.is_relative_to(ROOT) else str(source),
        "as_of": as_of,
        "nodes": nodes,
        "edges": edges,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Emit Dataset nodes/edges from mocked Snowflake extracts")
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_EXTRACT,
        help="Path to INFORMATION_SCHEMA-shaped JSON",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON",
    )
    args = parser.parse_args()
    payload = extract(args.input)
    indent = 2 if args.pretty else None
    print(json.dumps(payload, indent=indent))


if __name__ == "__main__":
    main()

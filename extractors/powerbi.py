"""
Power BI extractor stub.

Production shape: call the Admin Scanner API, resolve dataset datasources to
Snowflake FQNs, then emit Report / SemanticModel nodes and USES / BINDS edges.
This stub reads a mocked scanner payload — no live Power BI tenant required.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXTRACT = ROOT / "fixtures" / "powerbi_scanner.json"


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def snowflake_fqn(account: str, snowflake: dict[str, str]) -> str:
    return ".".join(
        part.lower()
        for part in (
            account,
            snowflake["database"],
            snowflake["schema"],
            snowflake["table"],
        )
    )


def extract(path: Path | None = None) -> dict[str, Any]:
    """Read scanner-shaped JSON and emit Report/SemanticModel graph fragments."""
    source = path or DEFAULT_EXTRACT
    raw = json.loads(source.read_text())
    account = raw.get("account", "acme").lower()
    as_of = raw.get("as_of", "1970-01-01")

    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []

    for workspace in raw.get("workspaces", []):
        workspace_id = workspace["id"]
        workspace_name = workspace.get("name", workspace_id)

        for dataset in workspace.get("datasets", []):
            model_id = f"{workspace_id}:{dataset['id']}"
            nodes.append(
                {
                    "label": "SemanticModel",
                    "id": model_id,
                    "properties": {
                        "name": dataset.get("name"),
                        "workspace_name": workspace_name,
                    },
                }
            )
            for usage in dataset.get("datasourceUsages", []):
                snowflake = usage.get("snowflake")
                if not snowflake:
                    continue
                dataset_fqn = snowflake_fqn(account, snowflake)
                edges.append(
                    {
                        "type": "USES",
                        "from": model_id,
                        "to": dataset_fqn,
                        "properties": {
                            "source": "powerbi_scanner",
                            "as_of": as_of,
                            "confidence": 1.0,
                            "extractor_version": "powerbi-stub-v0",
                        },
                    }
                )

        for report in workspace.get("reports", []):
            report_id = f"{workspace_id}:{report['id']}"
            model_id = f"{workspace_id}:{report['datasetId']}"
            nodes.append(
                {
                    "label": "Report",
                    "id": report_id,
                    "properties": {
                        "name": report.get("name"),
                        "workspace_name": workspace_name,
                        "criticality": report.get("criticality"),
                    },
                }
            )
            edges.append(
                {
                    "type": "BINDS",
                    "from": report_id,
                    "to": model_id,
                    "properties": {
                        "source": "powerbi_scanner",
                        "as_of": as_of,
                        "confidence": 1.0,
                        "extractor_version": "powerbi-stub-v0",
                    },
                }
            )
            # Also emit report → dataset USES via the bound model's datasources
            model_datasets = [
                e["to"]
                for e in edges
                if e["type"] == "USES" and e["from"] == model_id
            ]
            for dataset_fqn in model_datasets:
                edges.append(
                    {
                        "type": "USES",
                        "from": report_id,
                        "to": dataset_fqn,
                        "properties": {
                            "source": "powerbi_scanner",
                            "as_of": as_of,
                            "confidence": 1.0,
                            "extractor_version": "powerbi-stub-v0",
                        },
                    }
                )

    return {
        "extractor": "powerbi",
        "source_file": _rel(source),
        "as_of": as_of,
        "nodes": nodes,
        "edges": edges,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Emit Report/USES edges from mocked Power BI scanner extracts")
    parser.add_argument("--input", type=Path, default=DEFAULT_EXTRACT)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    payload = extract(args.input)
    print(json.dumps(payload, indent=2 if args.pretty else None))


if __name__ == "__main__":
    main()

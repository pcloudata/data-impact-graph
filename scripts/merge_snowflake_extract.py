#!/usr/bin/env python3
"""
Merge Snowflake extractor output into the showcase NetworkX graph.

Demonstrates the production ingest shape: extract → normalize → upsert graph.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from extractors.snowflake import extract as extract_snowflake
from impact_graph.apply_extract import apply_extract
from impact_graph.graph import build_graph, impact_for_dataset


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply Snowflake extractor fragments onto the demo graph")
    parser.add_argument(
        "--empty",
        action="store_true",
        help="Start from an empty graph instead of the full fixture graph",
    )
    parser.add_argument(
        "--dataset",
        default="acme.raw.sales.orders",
        help="Dataset id to print impact for after merge",
    )
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    import networkx as nx

    graph = nx.MultiDiGraph() if args.empty else build_graph()
    before_nodes, before_edges = graph.number_of_nodes(), graph.number_of_edges()

    payload = extract_snowflake()
    stats = apply_extract(graph, payload)

    result = {
        "extractor": payload["extractor"],
        "source_file": payload["source_file"],
        "before": {"nodes": before_nodes, "edges": before_edges},
        "applied": stats,
        "after": {"nodes": graph.number_of_nodes(), "edges": graph.number_of_edges()},
    }

    if args.empty:
        # On empty graph, impact needs Report/USES from elsewhere — just show lineage fragment
        derives = [
            (u, v)
            for u, v, data in graph.edges(data=True)
            if data.get("type") == "DERIVES_FROM"
        ]
        result["derives_from_edges"] = [{"from": u, "to": v} for u, v in sorted(derives)]
    else:
        try:
            result["impact"] = impact_for_dataset(graph, args.dataset)
        except KeyError:
            result["impact"] = {"error": f"unknown dataset: {args.dataset}"}

    print(json.dumps(result, indent=2 if args.pretty else None))


if __name__ == "__main__":
    main()

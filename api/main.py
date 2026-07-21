"""Minimal impact API over the in-memory showcase graph."""

from __future__ import annotations

import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from impact_graph.graph import build_graph, impact_for_dataset

app = FastAPI(
    title="data-impact-graph",
    description="Cross-stack blast radius for datasets (showcase API).",
    version="0.1.0",
)
GRAPH = build_graph()


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "nodes": GRAPH.number_of_nodes(),
        "edges": GRAPH.number_of_edges(),
    }


@app.get("/impact")
def impact(
    dataset: str = Query(
        ...,
        description="Snowflake-style dataset id, e.g. acme.raw.sales.orders",
        examples=["acme.raw.sales.orders"],
    ),
) -> dict:
    try:
        return impact_for_dataset(GRAPH, dataset)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown dataset: {dataset}") from exc

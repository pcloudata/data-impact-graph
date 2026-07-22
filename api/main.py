"""Minimal impact API over the in-memory showcase graph."""

from __future__ import annotations

import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from impact_graph.graph import build_graph, impact_for_dataset, list_datasets

WEB_DIR = ROOT / "web"

app = FastAPI(
    title="data-impact-graph",
    description="Cross-stack blast radius for datasets (showcase API).",
    version="0.2.0",
)
GRAPH = build_graph()


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "nodes": GRAPH.number_of_nodes(),
        "edges": GRAPH.number_of_edges(),
    }


@app.get("/datasets")
def datasets() -> dict:
    return {"datasets": list_datasets(GRAPH)}


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


@app.get("/")
def ui() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")


app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")

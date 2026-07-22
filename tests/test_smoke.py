"""Smoke tests for extractors, graph merge, and impact API."""

from __future__ import annotations

import sys
from pathlib import Path

import networkx as nx
import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.main import app
from extractors.jira import extract as extract_jira
from extractors.powerbi import extract as extract_powerbi
from extractors.snowflake import extract as extract_snowflake
from impact_graph.apply_extract import apply_extract
from impact_graph.graph import build_graph, impact_for_dataset


@pytest.fixture(scope="module")
def graph():
    return build_graph()


def test_snowflake_extractor_emits_datasets_and_lineage():
    payload = extract_snowflake()
    assert payload["extractor"] == "snowflake"
    assert any(n["id"] == "acme.raw.sales.orders" for n in payload["nodes"])
    assert any(
        e["type"] == "DERIVES_FROM"
        and e["from"] == "acme.curated.sales.orders"
        and e["to"] == "acme.raw.sales.orders"
        for e in payload["edges"]
    )


def test_powerbi_extractor_emits_reports_and_uses():
    payload = extract_powerbi()
    assert payload["extractor"] == "powerbi"
    assert any(n["id"] == "ws-finance:rpt-finance-close" and n["label"] == "Report" for n in payload["nodes"])
    assert any(
        e["type"] == "USES"
        and e["from"] == "ws-finance:rpt-finance-close"
        and e["to"] == "acme.analytics.mart.orders"
        for e in payload["edges"]
    )
    assert any(e["type"] == "BINDS" for e in payload["edges"])


def test_jira_extractor_emits_tickets_and_tracks():
    payload = extract_jira()
    assert payload["extractor"] == "jira"
    assert any(n["id"] == "DATA-450" and n["label"] == "Ticket" for n in payload["nodes"])
    assert any(
        e["type"] == "TRACKS"
        and e["from"] == "DATA-450"
        and e["to"] == "123456789012:us-east-1:glue:orders_etl"
        for e in payload["edges"]
    )


def test_apply_snowflake_extract_onto_empty_graph():
    g = nx.MultiDiGraph()
    stats = apply_extract(g, extract_snowflake())
    assert stats["nodes_upserted"] >= 7
    assert stats["edges_upserted"] >= 4
    assert g.nodes["acme.analytics.mart.orders"]["label"] == "Dataset"
    assert any(data.get("type") == "DERIVES_FROM" for _, _, data in g.edges(data=True))


def test_apply_powerbi_extract_links_report_to_dataset():
    g = nx.MultiDiGraph()
    apply_extract(g, extract_snowflake())
    apply_extract(g, extract_powerbi())
    assert g.has_edge("ws-finance:rpt-finance-close", "acme.analytics.mart.orders")
    edge_data = g.get_edge_data("ws-finance:rpt-finance-close", "acme.analytics.mart.orders")
    assert any(data.get("type") == "USES" for data in edge_data.values())


def test_impact_for_dataset(graph):
    payload = impact_for_dataset(graph, "acme.raw.sales.orders")
    assert payload["owner_team"] == "Finance Data"
    assert "acme.analytics.mart.orders" in payload["downstream_datasets"]
    assert any(r["name"] == "Finance Close" for r in payload["reports"])
    assert any(t["id"] == "DATA-450" for t in payload["open_tickets"])


def test_impact_api_ok():
    client = TestClient(app)
    response = client.get("/impact", params={"dataset": "acme.raw.sales.orders"})
    assert response.status_code == 200
    body = response.json()
    assert body["dataset"] == "acme.raw.sales.orders"
    assert any(r["name"] == "Finance Close" for r in body["reports"])
    assert any(t["id"] == "DATA-450" for t in body["open_tickets"])


def test_datasets_api():
    client = TestClient(app)
    response = client.get("/datasets")
    assert response.status_code == 200
    ids = [row["id"] for row in response.json()["datasets"]]
    assert "acme.raw.sales.orders" in ids


def test_ui_index():
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert "data-impact-graph" in response.text


def test_impact_api_404():
    client = TestClient(app)
    response = client.get("/impact", params={"dataset": "no.such.table"})
    assert response.status_code == 404


def test_health_api():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

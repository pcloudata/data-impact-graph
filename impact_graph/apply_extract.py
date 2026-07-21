"""Apply extractor graph fragments onto a NetworkX MultiDiGraph."""

from __future__ import annotations

from typing import Any

import networkx as nx


def apply_extract(graph: nx.MultiDiGraph, payload: dict[str, Any]) -> dict[str, int]:
    """
    Merge extractor output ({nodes, edges}) into an existing graph.

    Nodes are upserted (properties updated). Edges are keyed by type so
    re-running an extractor is idempotent for the same from/to/type triple.
    """
    nodes_upserted = 0
    edges_upserted = 0

    for node in payload.get("nodes", []):
        node_id = node["id"]
        props = dict(node.get("properties") or {})
        props["label"] = node["label"]
        if node_id in graph:
            graph.nodes[node_id].update(props)
        else:
            graph.add_node(node_id, **props)
        nodes_upserted += 1

    for edge in payload.get("edges", []):
        edge_type = edge["type"]
        src = edge["from"]
        dst = edge["to"]
        props = dict(edge.get("properties") or {})
        props["type"] = edge_type
        # Ensure endpoints exist even if extractor emitted edge-only refs
        if src not in graph:
            graph.add_node(src, label="Unknown")
        if dst not in graph:
            graph.add_node(dst, label="Dataset" if edge_type in {"DERIVES_FROM", "USES", "READS", "WRITES"} else "Unknown")
        graph.add_edge(src, dst, key=edge_type, **props)
        edges_upserted += 1

    return {"nodes_upserted": nodes_upserted, "edges_upserted": edges_upserted}

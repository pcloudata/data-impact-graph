"""Shared graph build and impact helpers for demos and the API."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import networkx as nx

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures"


def load_json(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


def edge_attrs(source: str, confidence: float = 1.0) -> dict:
    return {
        "source": source,
        "as_of": "2026-07-20",
        "confidence": confidence,
        "extractor_version": "fixtures-v0",
    }


def build_graph() -> nx.MultiDiGraph:
    g = nx.MultiDiGraph()
    teams = load_json("teams.json")
    github = load_json("github.json")
    aws = load_json("aws_jobs.json")
    snow = load_json("snowflake.json")
    pbi = load_json("powerbi.json")
    jira = load_json("jira.json")
    conf = load_json("confluence.json")

    for team in teams["teams"]:
        g.add_node(team["id"], label="Team", name=team["name"], cost_center=team["cost_center"])
        for member in team["members"]:
            g.add_node(member["id"], label="Person", name=member["name"], slack=member["slack"])
            g.add_edge(member["id"], team["id"], key="MEMBER_OF", type="MEMBER_OF", **edge_attrs("teams"))
        owns = team["owns"]
        for dataset_id in owns["datasets"]:
            g.add_edge(team["id"], dataset_id, key="OWNS", type="OWNS", **edge_attrs("teams"))
        for pipeline_id in owns["pipelines"]:
            g.add_edge(team["id"], pipeline_id, key="OWNS", type="OWNS", **edge_attrs("teams"))
        for report_id in owns["reports"]:
            g.add_edge(team["id"], report_id, key="OWNS", type="OWNS", **edge_attrs("teams"))
        for repo_id in owns["repositories"]:
            g.add_edge(team["id"], repo_id, key="OWNS", type="OWNS", **edge_attrs("teams"))

    for repo in github["repositories"]:
        g.add_node(
            repo["id"],
            label="Repository",
            url=repo["url"],
            default_branch=repo["default_branch"],
        )
        for pipeline_id in repo["implements_pipelines"]:
            g.add_edge(repo["id"], pipeline_id, key="IMPLEMENTS", type="IMPLEMENTS", **edge_attrs("github"))

    for job in aws["pipelines"]:
        g.add_node(
            job["id"],
            label="Pipeline",
            name=job["name"],
            tool=job["tool"],
            env=job["env"],
            schedule=job["schedule"],
            arn=job["arn"],
        )
        if job.get("repository"):
            g.add_edge(
                job["id"],
                job["repository"],
                key="DEPLOYS_FROM",
                type="DEPLOYS_FROM",
                **edge_attrs("aws_jobs"),
            )
        for dataset_id in job["reads"]:
            g.add_edge(job["id"], dataset_id, key="READS", type="READS", **edge_attrs("aws_jobs"))
        for dataset_id in job["writes"]:
            g.add_edge(job["id"], dataset_id, key="WRITES", type="WRITES", **edge_attrs("aws_jobs"))

    for dataset in snow["datasets"]:
        g.add_node(
            dataset["id"],
            label="Dataset",
            fq_name=dataset["id"],
            object_type=dataset["object_type"],
            layer=dataset["layer"],
            pii=dataset["pii"],
        )
        for upstream in dataset["upstream"]:
            g.add_edge(
                dataset["id"],
                upstream,
                key="DERIVES_FROM",
                type="DERIVES_FROM",
                **edge_attrs("snowflake"),
            )

    for model in pbi["semantic_models"]:
        g.add_node(
            model["id"],
            label="SemanticModel",
            name=model["name"],
            workspace_name=model["workspace_name"],
        )
        for dataset_id in model["snowflake_datasets"]:
            g.add_edge(model["id"], dataset_id, key="USES", type="USES", **edge_attrs("powerbi"))

    for report in pbi["reports"]:
        g.add_node(
            report["id"],
            label="Report",
            name=report["name"],
            workspace_name=report["workspace_name"],
            criticality=report["criticality"],
        )
        g.add_edge(
            report["id"],
            report["semantic_model"],
            key="BINDS",
            type="BINDS",
            **edge_attrs("powerbi"),
        )
        for dataset_id in report["snowflake_datasets"]:
            g.add_edge(report["id"], dataset_id, key="USES", type="USES", **edge_attrs("powerbi"))

    for ticket in jira["tickets"]:
        g.add_node(
            ticket["id"],
            label="Ticket",
            type=ticket["type"],
            status=ticket["status"],
            priority=ticket["priority"],
            url=ticket["url"],
        )
        for target in ticket["tracks"]:
            g.add_edge(ticket["id"], target["id"], key="TRACKS", type="TRACKS", **edge_attrs("jira"))

    for doc in conf["docs"]:
        g.add_node(doc["id"], label="Doc", title=doc["title"], url=doc["url"])
        for target in doc["describes"]:
            g.add_edge(doc["id"], target["id"], key="DESCRIBES", type="DESCRIBES", **edge_attrs("confluence"))

    for term in conf["glossary"]:
        g.add_node(
            term["id"],
            label="GlossaryTerm",
            definition=term["definition"],
            status=term["status"],
        )
        for dataset_id in term["defined_by_datasets"]:
            confidence = 0.6 if term["id"] == "campaign_roi" and "orders" in dataset_id else 1.0
            g.add_edge(
                dataset_id,
                term["id"],
                key="DEFINES",
                type="DEFINES",
                **edge_attrs("confluence", confidence=confidence),
            )

    return g


def nodes_by_label(g: nx.MultiDiGraph, label: str) -> list[str]:
    return [n for n, attrs in g.nodes(data=True) if attrs.get("label") == label]


def out_edges(g: nx.MultiDiGraph, node: str, edge_type: str) -> list[str]:
    return [v for _, v, data in g.out_edges(node, data=True) if data.get("type") == edge_type]


def in_edges(g: nx.MultiDiGraph, node: str, edge_type: str) -> list[str]:
    return [u for u, _, data in g.in_edges(node, data=True) if data.get("type") == edge_type]


def descendants_via_derives(g: nx.MultiDiGraph, root: str) -> set[str]:
    """Datasets downstream of root (nodes that DERIVES_FROM* root)."""
    found: set[str] = set()
    stack = [root]
    seen = {root}
    while stack:
        current = stack.pop()
        for downstream in in_edges(g, current, "DERIVES_FROM"):
            if downstream not in seen:
                seen.add(downstream)
                found.add(downstream)
                stack.append(downstream)
    return found


def impact_for_dataset(g: nx.MultiDiGraph, dataset_id: str) -> dict[str, Any]:
    """Blast-radius style payload for GET /impact."""
    if dataset_id not in g or g.nodes[dataset_id].get("label") != "Dataset":
        raise KeyError(dataset_id)

    downstream = sorted(descendants_via_derives(g, dataset_id))
    relevant = {dataset_id} | set(downstream)

    reports = []
    for report_id in nodes_by_label(g, "Report"):
        used = out_edges(g, report_id, "USES")
        if any(d in relevant for d in used):
            reports.append(
                {
                    "id": report_id,
                    "name": g.nodes[report_id].get("name"),
                    "criticality": g.nodes[report_id].get("criticality"),
                }
            )

    pipelines = []
    for pipeline_id in nodes_by_label(g, "Pipeline"):
        touched = out_edges(g, pipeline_id, "READS") + out_edges(g, pipeline_id, "WRITES")
        if any(d in relevant for d in touched):
            repos = in_edges(g, pipeline_id, "IMPLEMENTS") or out_edges(g, pipeline_id, "DEPLOYS_FROM")
            owners = in_edges(g, pipeline_id, "OWNS")
            pipelines.append(
                {
                    "id": pipeline_id,
                    "name": g.nodes[pipeline_id].get("name"),
                    "repository": repos[0] if repos else None,
                    "owner_team": g.nodes[owners[0]].get("name") if owners else None,
                }
            )

    owners = in_edges(g, dataset_id, "OWNS")
    return {
        "dataset": dataset_id,
        "layer": g.nodes[dataset_id].get("layer"),
        "pii": g.nodes[dataset_id].get("pii"),
        "owner_team": g.nodes[owners[0]].get("name") if owners else None,
        "downstream_datasets": downstream,
        "pipelines": sorted(pipelines, key=lambda item: item["name"] or ""),
        "reports": sorted(reports, key=lambda item: item["name"] or ""),
    }

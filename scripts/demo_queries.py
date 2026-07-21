#!/usr/bin/env python3
"""Build an in-memory NetworkX graph from fixtures and run the demo query pack."""

from __future__ import annotations

import json
from pathlib import Path

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
    return [
        v
        for _, v, data in g.out_edges(node, data=True)
        if data.get("type") == edge_type
    ]


def in_edges(g: nx.MultiDiGraph, node: str, edge_type: str) -> list[str]:
    return [
        u
        for u, _, data in g.in_edges(node, data=True)
        if data.get("type") == edge_type
    ]


def descendants_via_derives(g: nx.MultiDiGraph, root: str) -> set[str]:
    """Datasets that DERIVES_FROM* root (downstream points at upstream)."""
    found: set[str] = set()
    stack = [root]
    seen = {root}
    while stack:
        current = stack.pop()
        for upstream_ref in in_edges(g, current, "DERIVES_FROM"):
            # upstream_ref is downstream dataset that derives from current
            if upstream_ref not in seen:
                seen.add(upstream_ref)
                found.add(upstream_ref)
                stack.append(upstream_ref)
    return found


def query_blast_radius(g: nx.MultiDiGraph) -> None:
    root = "acme.raw.sales.orders"
    downstream = descendants_via_derives(g, root)
    relevant = {root} | downstream
    reports = sorted(
        {
            g.nodes[r].get("name", r)
            for r in nodes_by_label(g, "Report")
            if any(d in relevant for d in out_edges(g, r, "USES"))
        }
    )
    pipelines = sorted(
        {
            g.nodes[j].get("name", j)
            for j in nodes_by_label(g, "Pipeline")
            if any(d in relevant for d in out_edges(g, j, "READS") + out_edges(g, j, "WRITES"))
        }
    )
    print("01 blast_radius")
    print(f"  root: {root}")
    print(f"  downstream_datasets: {sorted(downstream)}")
    print(f"  reports: {reports}")
    print(f"  pipelines: {pipelines}")


def query_orphan_datasets(g: nx.MultiDiGraph) -> None:
    owned = {v for _, v, data in g.edges(data=True) if data.get("type") == "OWNS"}
    orphans = sorted(d for d in nodes_by_label(g, "Dataset") if d not in owned)
    print("02 orphan_datasets")
    for dataset_id in orphans:
        print(f"  {dataset_id} layer={g.nodes[dataset_id].get('layer')}")


def query_p1_risk(g: nx.MultiDiGraph) -> None:
    print("03 p1_risk_open_bugs")
    for ticket_id in nodes_by_label(g, "Ticket"):
        ticket = g.nodes[ticket_id]
        if ticket.get("type") != "Bug":
            continue
        if ticket.get("status", "").lower() not in {"open", "in progress"}:
            continue
        for pipeline_id in out_edges(g, ticket_id, "TRACKS"):
            if g.nodes.get(pipeline_id, {}).get("label") != "Pipeline":
                continue
            for dataset_id in out_edges(g, pipeline_id, "WRITES"):
                for report_id in in_edges(g, dataset_id, "USES"):
                    if g.nodes.get(report_id, {}).get("label") != "Report":
                        continue
                    if g.nodes[report_id].get("criticality") != "P1":
                        continue
                    print(
                        f"  {ticket_id} -> {g.nodes[pipeline_id].get('name')} -> "
                        f"{dataset_id} -> {g.nodes[report_id].get('name')} (P1)"
                    )


def query_report_to_repo(g: nx.MultiDiGraph) -> None:
    report_id = "ws-finance:rpt-finance-close"
    print("04 report_to_repo")
    for dataset_id in out_edges(g, report_id, "USES"):
        pipelines = in_edges(g, dataset_id, "WRITES")
        owners = in_edges(g, dataset_id, "OWNS")
        for pipeline_id in pipelines:
            repos = in_edges(g, pipeline_id, "IMPLEMENTS") or out_edges(g, pipeline_id, "DEPLOYS_FROM")
            print(
                f"  report={g.nodes[report_id].get('name')} dataset={dataset_id} "
                f"pipeline={g.nodes[pipeline_id].get('name')} "
                f"repo={repos[0] if repos else None} "
                f"owner={g.nodes[owners[0]].get('name') if owners else None}"
            )


def query_glossary_drift(g: nx.MultiDiGraph) -> None:
    print("05 glossary_drift")
    for term_id in nodes_by_label(g, "GlossaryTerm"):
        datasets = in_edges(g, term_id, "DEFINES")
        if len(datasets) > 1:
            print(f"  {term_id} status={g.nodes[term_id].get('status')} datasets={sorted(datasets)}")


def query_pipelines_without_repo(g: nx.MultiDiGraph) -> None:
    print("06 pipelines_without_repo")
    for pipeline_id in nodes_by_label(g, "Pipeline"):
        has_repo = bool(out_edges(g, pipeline_id, "DEPLOYS_FROM") or in_edges(g, pipeline_id, "IMPLEMENTS"))
        if not has_repo:
            print(f"  {g.nodes[pipeline_id].get('name')} ({pipeline_id})")


def query_pii_to_bi(g: nx.MultiDiGraph) -> None:
    print("07 pii_to_bi")
    for report_id in nodes_by_label(g, "Report"):
        pii_ids: set[str] = set()
        for dataset_id in out_edges(g, report_id, "USES"):
            stack = [dataset_id]
            seen = {dataset_id}
            while stack:
                current = stack.pop()
                if g.nodes[current].get("pii"):
                    pii_ids.add(current)
                for upstream in out_edges(g, current, "DERIVES_FROM"):
                    if upstream not in seen:
                        seen.add(upstream)
                        stack.append(upstream)
        if pii_ids:
            print(
                f"  {g.nodes[report_id].get('name')} "
                f"({g.nodes[report_id].get('criticality')}): {sorted(pii_ids)}"
            )


def query_ownership_coverage(g: nx.MultiDiGraph) -> None:
    print("08 ownership_coverage")
    counts: dict[str, list[str]] = {}
    owned = set()
    for team_id, dataset_id, data in g.edges(data=True):
        if data.get("type") != "OWNS":
            continue
        if g.nodes.get(dataset_id, {}).get("label") != "Dataset":
            continue
        owned.add(dataset_id)
        owner = g.nodes[team_id].get("name", team_id)
        counts.setdefault(owner, []).append(dataset_id)
    unowned = [d for d in nodes_by_label(g, "Dataset") if d not in owned]
    counts["(unowned)"] = unowned
    for owner, datasets in sorted(counts.items(), key=lambda item: (-len(item[1]), item[0])):
        print(f"  {owner}: {len(datasets)} -> {datasets[:5]}")


def main() -> None:
    graph = build_graph()
    print(f"Loaded graph: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges\n")
    query_blast_radius(graph)
    print()
    query_orphan_datasets(graph)
    print()
    query_p1_risk(graph)
    print()
    query_report_to_repo(graph)
    print()
    query_glossary_drift(graph)
    print()
    query_pipelines_without_repo(graph)
    print()
    query_pii_to_bi(graph)
    print()
    query_ownership_coverage(graph)


if __name__ == "__main__":
    main()

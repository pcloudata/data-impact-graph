#!/usr/bin/env python3
"""Build an in-memory NetworkX graph from fixtures and run the demo query pack."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from impact_graph.graph import (  # noqa: E402
    build_graph,
    descendants_via_derives,
    in_edges,
    nodes_by_label,
    out_edges,
)


def query_blast_radius(g) -> None:
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


def query_orphan_datasets(g) -> None:
    owned = {v for _, v, data in g.edges(data=True) if data.get("type") == "OWNS"}
    orphans = sorted(d for d in nodes_by_label(g, "Dataset") if d not in owned)
    print("02 orphan_datasets")
    for dataset_id in orphans:
        print(f"  {dataset_id} layer={g.nodes[dataset_id].get('layer')}")


def query_p1_risk(g) -> None:
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


def query_report_to_repo(g) -> None:
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


def query_glossary_drift(g) -> None:
    print("05 glossary_drift")
    for term_id in nodes_by_label(g, "GlossaryTerm"):
        datasets = in_edges(g, term_id, "DEFINES")
        if len(datasets) > 1:
            print(f"  {term_id} status={g.nodes[term_id].get('status')} datasets={sorted(datasets)}")


def query_pipelines_without_repo(g) -> None:
    print("06 pipelines_without_repo")
    for pipeline_id in nodes_by_label(g, "Pipeline"):
        has_repo = bool(out_edges(g, pipeline_id, "DEPLOYS_FROM") or in_edges(g, pipeline_id, "IMPLEMENTS"))
        if not has_repo:
            print(f"  {g.nodes[pipeline_id].get('name')} ({pipeline_id})")


def query_pii_to_bi(g) -> None:
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


def query_ownership_coverage(g) -> None:
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

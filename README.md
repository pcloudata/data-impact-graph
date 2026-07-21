# data-impact-graph

Cross-stack **impact, ownership, and lineage** for data platform teams — modeled as a minimal property graph over Jira, Confluence, GitHub, AWS, Snowflake, and Power BI.

This is a **showcase / reference design**, not a production catalog. It answers questions like:

- If we change `RAW.ORDERS`, what pipelines, tables, and Power BI reports break?
- Which datasets have no owning team?
- Which open Jira bugs track jobs that feed P1 reports?

## Interview talk track (30–60s)

**Problem.** Platform work spans Jira, Confluence, GitHub, AWS, Snowflake, and Power BI. Blast radius is tribal knowledge.

**Graph.** Encode those systems as nodes and typed edges (owns, writes, derives_from, uses, tracks) with stable IDs and provenance.

**Punchline.** Change impact on `acme.raw.sales.orders` surfaces curated/mart tables, `orders_etl`, and P1 **Finance Close** in one hop path — see [docs/screenshots/demo_queries.txt](docs/screenshots/demo_queries.txt).

> Full script: [docs/talk-track.md](docs/talk-track.md)

## When *not* to build this

Prefer Snowflake native lineage + a data catalog (DataHub, OpenMetadata, Alation) + Confluence glossary when:

- Pain is mostly “find the right table/doc,” not multi-hop impact across tickets/repos/jobs/BI
- One warehouse and one orchestrator already cover ~80% of lineage questions
- Nobody will own edge freshness (entity resolution, schema drift)
- Success = better dashboards, not safer changes or clearer ownership

Build (or extend a catalog graph) when change impact routinely crosses **AWS → Snowflake → Power BI → Jira/GitHub**, and ownership is fragmented across CODEOWNERS, warehouse tags, and tickets.

## Quick start

### Option A — Neo4j (recommended for demos)

```bash
# Requires Docker
docker compose up -d

# Load schema constraints + seed data
cat graph/constraints.cypher graph/seed.cypher | docker compose exec -T neo4j cypher-shell -u neo4j -p impactgraph

# Run a sample query
docker compose exec neo4j cypher-shell -u neo4j -p impactgraph -f /var/lib/neo4j/import/queries/01_blast_radius.cypher
```

Browser UI: [http://localhost:7474](http://localhost:7474) — user `neo4j` / password `impactgraph`.

### Option B — No Docker (Python walkthrough)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/demo_queries.py
```

### Option C — Impact API

```bash
source .venv/bin/activate
uvicorn api.main:app --reload --port 8000
curl "http://127.0.0.1:8000/impact?dataset=acme.raw.sales.orders"
```

Sample response: [docs/screenshots/impact_api.json](docs/screenshots/impact_api.json).

### Snowflake extractor stub

```bash
python -m extractors.snowflake --pretty
```

Reads mocked INFORMATION_SCHEMA-shaped JSON and emits `Dataset` nodes + `DERIVES_FROM` edges (production path without live credentials).

## What’s in the box

| Path | Purpose |
|------|---------|
| [`docs/schema.md`](docs/schema.md) | v0 node/edge types + ID conventions |
| [`docs/ingest-map.md`](docs/ingest-map.md) | Mock source → graph mapping |
| [`docs/go-no-go.md`](docs/go-no-go.md) | Leadership checklist |
| [`docs/talk-track.md`](docs/talk-track.md) | 30–60s interview script |
| [`docs/screenshots/`](docs/screenshots/) | Captured demo + API output |
| [`graph/seed.cypher`](graph/seed.cypher) | Synthetic but realistic demo graph |
| [`graph/queries/`](graph/queries/) | Impact / ownership / governance Cypher |
| [`fixtures/`](fixtures/) | JSON stand-ins for tool extracts |
| [`extractors/snowflake.py`](extractors/snowflake.py) | INFORMATION_SCHEMA → graph stub |
| [`api/main.py`](api/main.py) | FastAPI `GET /impact` |
| [`scripts/demo_queries.py`](scripts/demo_queries.py) | Docker-free query demo |
| [`.github/workflows/ci.yml`](.github/workflows/ci.yml) | Runs demo + extractor smoke tests |

## Example blast radius

```text
Jira DATA-123 ──TRACKS──▶ Confluence Spec
                              │
                              DESCRIBES
                              ▼
GitHub data-platform ──IMPLEMENTS──▶ Glue orders_etl ──WRITES──▶ ANALYTICS.ORDERS
                                                                      ▲
RAW.ORDERS ──────────────────────────DERIVES_FROM─────────────────────┘
                                                                      │
Team Finance Data ──OWNS──▶ ANALYTICS.ORDERS ◀──USES── Power BI Finance Close
```

## Design principles

1. **IDs over names** — Snowflake FQNs, ARNs, Power BI IDs, issue keys; names are display-only.
2. **Edges carry provenance** — `source`, `as_of`, `confidence` on every relationship.
3. **Table-level first** — column lineage is v0.5+ (noisy and expensive).
4. **Catalog-friendly** — this graph complements a catalog; it does not replace Snowflake or Power BI.

## Profile pin (manual)

Repo topics are set (`data-engineering`, `lineage`, `knowledge-graph`, `snowflake`, `neo4j`). GitHub does not expose a stable public API to pin repos on a profile — pin it in the UI:

1. Open https://github.com/pcloudata
2. Customize pinned repositories → select **data-impact-graph**

## License

MIT

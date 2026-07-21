# Interview talk track (30–60 seconds)

**Problem.** Data platform teams live across Jira, Confluence, GitHub, AWS, Snowflake, and Power BI. “If we change this table, what breaks?” is tribal knowledge.

**Approach.** Model those systems as a small property graph: datasets, pipelines, reports, tickets, docs, and owners — with stable IDs and provenance on every edge.

**Proof.** Ask for blast radius on `acme.raw.sales.orders` and you get curated/mart tables, the `orders_etl` job, and the P1 **Finance Close** report — without opening six tools.

```text
01 blast_radius
  root: acme.raw.sales.orders
  downstream_datasets: ['acme.analytics.mart.orders', 'acme.analytics.mart.orphan_metrics', 'acme.curated.sales.orders']
  reports: ['Finance Close']
  pipelines: ['orders_etl']
```

See also: [demo query output](screenshots/demo_queries.txt) and [sample `/impact` JSON](screenshots/impact_api.json).

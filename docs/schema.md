# Schema v0 — data-impact-graph

Labeled property graph for cross-stack **impact, ownership, and lineage**. Keep it small: ~10 node types, ~12 edge types.

## Node types

| Label | Stable `id` | Key properties | Source of truth |
|-------|-------------|----------------|-----------------|
| `Person` | email (lowercase) | `name`, `slack` | IdP / HR / GitHub |
| `Team` | slug (`finance-data`) | `name`, `cost_center` | Org chart / GitHub team |
| `Repository` | `org/repo` | `url`, `default_branch` | GitHub |
| `Pipeline` | AWS ARN or `account:region:job_name` | `name`, `schedule`, `env`, `tool` | Glue / MWAA / Step Functions |
| `Dataset` | `account.db.schema.object` (lowercase) | `layer`, `pii`, `object_type` | Snowflake |
| `Report` | `workspace_id:report_id` | `name`, `workspace_name`, `criticality` | Power BI |
| `SemanticModel` | `workspace_id:dataset_id` | `name` | Power BI dataset |
| `Ticket` | issue key (`DATA-123`) | `status`, `type`, `priority`, `url` | Jira |
| `Doc` | `space:page_id` | `title`, `url` | Confluence |
| `GlossaryTerm` | slug (`revenue`) | `definition`, `status` | Confluence / catalog |

`Column` is deferred to v0.5.

## Edge types

| Type | From → To | Meaning |
|------|-----------|---------|
| `MEMBER_OF` | Person → Team | Team membership |
| `OWNS` | Team → Dataset \| Pipeline \| Report \| Repository | Accountability |
| `IMPLEMENTS` | Repository → Pipeline | Code that runs the job |
| `DEPLOYS_FROM` | Pipeline → Repository | Inverse deploy link (optional if `IMPLEMENTS` exists) |
| `READS` | Pipeline → Dataset | Job reads table/view |
| `WRITES` | Pipeline → Dataset | Job writes table/view |
| `DERIVES_FROM` | Dataset → Dataset | Table-level lineage (downstream → upstream) |
| `USES` | Report \| SemanticModel → Dataset | BI consumption |
| `BINDS` | Report → SemanticModel | Report bound to dataset |
| `TRACKS` | Ticket → Dataset \| Pipeline \| Report \| Doc | Work item linkage |
| `DESCRIBES` | Doc → Dataset \| GlossaryTerm \| Report | Documentation |
| `DEFINES` | Dataset → GlossaryTerm | Physical asset implements a business term |

## Edge properties (required on every relationship)

| Property | Example | Why |
|----------|---------|-----|
| `source` | `snowflake_deps`, `pbi_scanner`, `manual` | Provenance |
| `as_of` | `2026-07-20` | Freshness |
| `confidence` | `1.0` / `0.6` | ID match vs fuzzy name match |
| `extractor_version` | `fixtures-v0` | Reproducibility |

## Identity rules

1. Prefer API IDs over display names.
2. Normalize Snowflake IDs to lowercase `account.db.schema.object`.
3. Power BI names are display-only; always key by workspace + object id.
4. Soft / name-matched edges must use `confidence < 1.0`.
5. Never invent joins in docs — only emit `DERIVES_FROM` / `USES` from extractors or reviewed fixtures.

## Non-goals for v0

- Column-level lineage
- Full RDF/OWL ontology
- Real-time streaming ingest
- Replacing Snowflake, dbt, or Power BI semantic models

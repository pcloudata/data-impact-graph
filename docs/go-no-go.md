# Go / no-go checklist

Use this with platform leadership before investing in a custom knowledge graph.

## Go — proceed (or extend a catalog’s graph)

- [ ] “If we change X, what breaks?” regularly spans jobs, warehouse, BI, and tickets
- [ ] Ownership is inconsistent across CODEOWNERS, Snowflake tags, and Jira components
- [ ] P1 reports lack a reliable path back to producing jobs and owners
- [ ] AI / search over Confluence invents joins and owners
- [ ] A named owner will maintain extractors and entity resolution for 6+ months
- [ ] Success metric is safer changes / clearer accountability (not prettier dashboards)

## No-go — use catalog + native lineage instead

- [ ] Lineage inside Snowflake / dbt already answers most impact questions
- [ ] Single orchestrator and warehouse; little cross-tool glue
- [ ] No bandwidth for ID hygiene (FQNs, ARNs, Power BI IDs)
- [ ] Goal is discovery/search only → buy/adopt DataHub, OpenMetadata, or Alation
- [ ] Column-level lineage demanded on day one (defer; start table-level)

## Phased rollout (recommended)

| Phase | Scope | Exit criteria |
|-------|-------|---------------|
| 0 | This demo schema + seed + queries | Stakeholders agree the *questions* matter |
| 1 | Catalog for datasets + owners + warehouse lineage | Orphan datasets visible; basic blast radius in warehouse |
| 2 | Add edges catalogs handle poorly: ticket↔asset, report↔job | P1 report → job → repo path queryable |
| 3 | Optional custom graph store / API if catalog graph is insufficient | Impact API used in change process |

## Cost reality

- **Cheap:** schema design, seed demo, catalog adoption
- **Expensive:** fuzzy entity resolution, keeping Power BI ↔ Snowflake edges fresh, org politics on “who owns what”
- **Avoid:** boiling the ocean with enterprise OWL before five queries deliver value

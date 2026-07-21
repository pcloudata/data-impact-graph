# Ingest map (mock sources → graph)

v0 uses **JSON fixtures** under [`fixtures/`](../fixtures/) instead of live APIs. Production extractors would call the same logical fields.

| Fixture | Produces nodes | Produces edges |
|---------|----------------|----------------|
| `teams.json` | `Team`, `Person` | `MEMBER_OF`, `OWNS` (declared) |
| `github.json` | `Repository` | `OWNS` (from CODEOWNERS), `IMPLEMENTS` |
| `aws_jobs.json` | `Pipeline` | `READS`, `WRITES`, `DEPLOYS_FROM` |
| `snowflake.json` | `Dataset` | `DERIVES_FROM` |
| `powerbi.json` | `Report`, `SemanticModel` | `BINDS`, `USES` |
| `jira.json` | `Ticket` | `TRACKS` |
| `confluence.json` | `Doc`, `GlossaryTerm` | `DESCRIBES`, `DEFINES` |

## Field mapping (highlights)

### Snowflake → `Dataset`

- `fq_name` → `id` / `fq_name`
- `layer` → `raw` \| `curated` \| `mart`
- `pii` → boolean
- `upstream`[] → `DERIVES_FROM` edges (this dataset derives from each upstream)

### AWS Glue / jobs → `Pipeline`

- `arn` or `account:region:name` → `id`
- `reads`[] / `writes`[] → dataset FQNs → `READS` / `WRITES`
- `repository` → `IMPLEMENTS` / `DEPLOYS_FROM`

### Power BI → `Report` / `SemanticModel`

- `workspace_id` + `report_id` / `dataset_id` → composite `id`
- `snowflake_datasets`[] → `USES`

### GitHub → `Repository`

- `full_name` → `id`
- `codeowners` team slug → `OWNS`
- `implements_pipeline` → `IMPLEMENTS`

### Jira → `Ticket`

- `key` → `id`
- `tracks`[] `{type, id}` → `TRACKS`

### Confluence → `Doc` / `GlossaryTerm`

- `space` + `page_id` → `Doc.id`
- `describes`[] → `DESCRIBES`
- glossary entries → `GlossaryTerm` + `DEFINES` from datasets

## Provenance defaults for fixtures

```json
{
  "source": "<fixture_basename>",
  "as_of": "2026-07-20",
  "confidence": 1.0,
  "extractor_version": "fixtures-v0"
}
```

Name-only Power BI → Snowflake matches in real life should drop `confidence` (e.g. `0.6`) until confirmed via scanner API.

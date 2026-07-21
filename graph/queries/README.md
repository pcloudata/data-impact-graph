# Expected answers for the Cypher query pack (fixtures-v0)

| Query | Intent | Expected highlights |
|-------|--------|---------------------|
| `01_blast_radius` | Downstream of `acme.raw.sales.orders` | `curated.sales.orders`, `analytics.mart.orders`, `orphan_metrics`; report **Finance Close**; pipeline **orders_etl** |
| `02_orphan_datasets` | No `OWNS` edge | `acme.raw.marketing.campaigns`, `acme.analytics.mart.campaign_roi`, `acme.analytics.mart.orphan_metrics` |
| `03_p1_risk_open_bugs` | Open bugs on P1 feeders | **DATA-450** → `orders_etl` → **Finance Close** |
| `04_report_to_repo` | Report → repo path | Finance Close → `analytics.mart.orders` → `orders_etl` → `acme-corp/data-platform` → Finance Data |
| `05_glossary_drift` | Term with multiple DEFINES | `campaign_roi` ← orders mart + campaign_roi mart |
| `06_pipelines_without_repo` | Shadow jobs | `orphan_campaign_load` |
| `07_pii_to_bi` | PII upstream of BI | Finance Close path includes raw/curated orders (`pii: true`) |
| `08_ownership_coverage` | Owner rollup | Finance Data and Platform own some; `(unowned)` has 3 datasets |

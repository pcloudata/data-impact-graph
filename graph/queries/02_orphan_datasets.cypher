// 02 — Datasets with no owning team
// Expected: raw.marketing.campaigns, analytics.mart.campaign_roi, analytics.mart.orphan_metrics
MATCH (d:Dataset)
WHERE NOT ()-[:OWNS]->(d)
RETURN d.id AS orphan_dataset, d.layer AS layer, d.pii AS pii
ORDER BY d.id;

// 07 — PII datasets feeding BI reports
// Expected: raw/curated orders (pii) upstream of Finance Close via lineage + USES
MATCH (rpt:Report)-[:USES]->(d:Dataset)
OPTIONAL MATCH (d)-[:DERIVES_FROM*0..5]->(upstream:Dataset)
WHERE upstream.pii = true OR d.pii = true
WITH rpt, collect(DISTINCT CASE WHEN upstream.pii THEN upstream.id END) +
          CASE WHEN d.pii THEN [d.id] ELSE [] END AS pii_datasets
RETURN rpt.name AS report,
       rpt.criticality AS criticality,
       [x IN pii_datasets WHERE x IS NOT NULL | x] AS pii_in_path
ORDER BY rpt.name;

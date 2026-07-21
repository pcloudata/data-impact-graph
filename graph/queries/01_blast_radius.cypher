// 01 — Blast radius from RAW.ORDERS
// Expected: curated + mart orders, orphan_metrics view, Finance Close report, orders_etl pipeline
MATCH (root:Dataset {id: 'acme.raw.sales.orders'})
OPTIONAL MATCH path = (down:Dataset)-[:DERIVES_FROM*1..5]->(root)
WITH root, collect(DISTINCT down) AS downstream_datasets
OPTIONAL MATCH (rpt:Report)-[:USES]->(d:Dataset)
WHERE d = root OR d IN downstream_datasets
OPTIONAL MATCH (j:Pipeline)-[:READS|WRITES]->(d2:Dataset)
WHERE d2 = root OR d2 IN downstream_datasets
RETURN root.id AS root,
       [x IN downstream_datasets | x.id] AS downstream_datasets,
       collect(DISTINCT rpt.name) AS reports,
       collect(DISTINCT j.name) AS pipelines;

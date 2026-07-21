// 08 — Team ownership coverage summary
MATCH (d:Dataset)
OPTIONAL MATCH (t:Team)-[:OWNS]->(d)
RETURN coalesce(t.name, '(unowned)') AS owner,
       count(d) AS dataset_count,
       collect(d.id)[..5] AS sample_datasets
ORDER BY dataset_count DESC;

// 06 — Pipelines with no repository link (undeployed / shadow jobs)
// Expected: orphan_campaign_load
MATCH (j:Pipeline)
WHERE NOT (j)-[:DEPLOYS_FROM]->(:Repository)
  AND NOT (:Repository)-[:IMPLEMENTS]->(j)
RETURN j.id AS pipeline_id, j.name AS name, j.env AS env
ORDER BY j.name;

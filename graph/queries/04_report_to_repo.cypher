// 04 — End-to-end path: report → dataset → job → repo → owners
// Expected path for Finance Close
MATCH (rpt:Report {id: 'ws-finance:rpt-finance-close'})-[:USES]->(d:Dataset)
OPTIONAL MATCH (j:Pipeline)-[:WRITES]->(d)
OPTIONAL MATCH (r:Repository)-[:IMPLEMENTS]->(j)
OPTIONAL MATCH (t:Team)-[:OWNS]->(d)
RETURN rpt.name AS report,
       d.id AS dataset,
       j.name AS pipeline,
       r.id AS repository,
       t.name AS owning_team;

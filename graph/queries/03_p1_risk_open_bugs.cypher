// 03 — Open bugs on pipelines that feed P1 reports
// Expected: DATA-450 → orders_etl → Finance Close (P1)
MATCH (tk:Ticket)-[:TRACKS]->(j:Pipeline)-[:WRITES]->(d:Dataset)<-[:USES]-(rpt:Report)
WHERE tk.type = 'Bug'
  AND toLower(tk.status) IN ['open', 'in progress']
  AND rpt.criticality = 'P1'
RETURN tk.id AS ticket,
       tk.priority AS priority,
       j.name AS pipeline,
       d.id AS dataset,
       rpt.name AS report,
       rpt.criticality AS criticality;

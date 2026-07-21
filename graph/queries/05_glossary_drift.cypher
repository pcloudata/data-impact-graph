// 05 — Glossary term defined by multiple datasets (definition drift signal)
// Expected: campaign_roi linked to campaign_roi mart AND orders mart
MATCH (g:GlossaryTerm)<-[:DEFINES]-(d:Dataset)
WITH g, collect(d.id) AS datasets
WHERE size(datasets) > 1
RETURN g.id AS term, g.status AS status, datasets
ORDER BY g.id;

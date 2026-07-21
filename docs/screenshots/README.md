# Screenshots / captured output

Generated from the showcase graph (no Neo4j required):

| File | What it shows |
|------|----------------|
| [`demo_queries.txt`](demo_queries.txt) | Full demo query pack terminal output |
| [`impact_api.json`](impact_api.json) | Sample `GET /impact?dataset=acme.raw.sales.orders` response |

Regenerate:

```bash
python scripts/demo_queries.py > docs/screenshots/demo_queries.txt
python - <<'PY'
import json
from impact_graph.graph import build_graph, impact_for_dataset
print(json.dumps(impact_for_dataset(build_graph(), "acme.raw.sales.orders"), indent=2))
PY
```

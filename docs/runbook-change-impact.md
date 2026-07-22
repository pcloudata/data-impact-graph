# Change-request runbook — blast radius before you merge

Use this when a PR changes a Snowflake table (drop/rename column, filter logic, grain change). The point is to **know who breaks and who to ping** before merge — not after Finance Slack lights up.

## Scenario

Engineer opens a PR against `acme-corp/data-platform` that alters `RAW.SALES.ORDERS` (example: drop `customer_email` or change order grain).

## 1. Identify the dataset id

Stable id convention (lowercase FQN):

```text
acme.raw.sales.orders
```

## 2. Ask the impact API

```bash
cd /path/to/data-impact-graph
source .venv/bin/activate
uvicorn api.main:app --port 8000
```

```bash
curl -s "http://127.0.0.1:8000/impact?dataset=acme.raw.sales.orders" | python3 -m json.tool
```

Or open the UI: [http://127.0.0.1:8000/](http://127.0.0.1:8000/) → pick the dataset → **Run impact**.

## 3. Read the response like a change ticket

| Field | What to do |
|-------|------------|
| `owner_team` | Primary ping for approval / rollback owner |
| `downstream_datasets` | Tables/views that inherit the change |
| `pipelines` | Jobs to re-test; note `repository` for CODEOWNERS |
| `reports` | Especially anything `criticality: P1` (block merge without sign-off) |
| `open_tickets` | Existing Bugs/Stories already tracking this blast radius — avoid duplicate work |

Example punchline from the showcase graph:

- Owner: **Finance Data**
- Downstream: curated + mart orders (+ orphan metrics view)
- Pipeline: **orders_etl** in `acme-corp/data-platform`
- Report: **Finance Close (P1)**
- Open ticket: **DATA-450** on the same pipeline/report path

## 4. Who to ping (checklist)

1. Owning team (`owner_team`) in Slack / on-call rotation  
2. CODEOWNERS on each listed `repository`  
3. Report owners / BI stakeholders for every **P1** report  
4. Assignees on related `open_tickets` (don’t open a twin bug)

## 5. Merge gate (suggested)

- [ ] Impact JSON attached to the PR  
- [ ] P1 report owners acknowledged  
- [ ] Pipeline dry-run / contract test planned  
- [ ] Rollback note (revert PR or restore column) written

## Why this beats Confluence search

Docs answer “what is this table?”  
The graph answers “**if we change it Tuesday night, who pages Wednesday morning?**”

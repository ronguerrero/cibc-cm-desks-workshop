# R5 — "How do I share my data product to the org?"

Once your assets are governed, share up through both front doors. Proven in Phase 4.

## 1. Certify + bound the product as a domain
```sql
ALTER TABLE <cat>.<schema>.my_gold SET TAGS ('system.certification_status'='certified');
```
Create a Discover domain (data-product boundary + Genie One discovery signal):
```bash
databricks api post /api/2.1/tag-policies --json '{"tag_key":"My Desk","description":"...","values":[{"name":"true"}]}'
databricks api post /api/2.0/domains      --json '{"display_name":"My Desk","tag_key":"My Desk","owner_ids":[<numeric_user_id>]}'
```
```sql
ALTER TABLE <cat>.<schema>.my_gold SET TAGS ('My Desk'='true');   -- tag every asset in the product
```
(tag_key: no `&` → "and"; `/` = subdomain separator. Domains = Public Preview.)

## 2a. Front door A — Genie One (broad, rank-based discovery)
**No registration API.** Genie One auto-discovers every certified space / metric view / KA the user
can access and ranks via OntoRank. You influence it only through: space **name + description**
(top lever), **certification** (authority), **domain tags** (context), **grants/RLS** (per-user).
Enroll Genie One + its chat/routing preview. Set expectations: routing is Public Preview + stochastic;
Genie + KA composition is Private Preview (single space) — use the Copilot for reliable composition.

## 2b. Front door B — Capital Markets Copilot (deterministic, supervisor-of-supervisors)
Register your desk agent as a sub-agent of the org Copilot (see
`federation/01_copilot_supervisor_of_supervisors.py`). Raw REST (SDK Tool lacks the spec field):
```bash
databricks api post "/api/2.1/supervisor-agents/<copilot_id>/tools?tool_id=my-desk" --json '{
  "tool_type":"supervisor_agent","name":"my_desk_agent","description":"...",
  "supervisor_agent":{"supervisor_agent_id":"<my_desk_supervisor_id>"}}'
```

## ✓ Validation
A cross-desk question to the Copilot routes to your desk agent and composes with others. In this
build: "AC oil exposure + WTI −10% PnL AND house view on fuel hedging" → Portfolio + Research desks,
synthesized, with masks/RLS intact through every hop.

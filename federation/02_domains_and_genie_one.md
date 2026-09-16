# Phase 4 · Federation — Discover domains + Genie One (front door A)

## Discover domains (data-product boundaries) — built live
One governed domain per desk (a governed **tag** + a Discover **domain**), assets tagged in.

| Desk | tag_key / domain | domain_id | tagged assets |
|---|---|---|---|
| Portfolio | `CM Portfolio and Exposure` | `65bd9c6a-7b16-4cbf-af83-3f9b2da45df5` | positions, clients, exposure_kpis, get_client_positions, compute_shock_pnl |
| Research | `CM Research and Filings` | `a45eaf62-8138-4e58-a387-3cc92d4334c9` | research_docs, get_filing_facts |
| Market Intel | `CM Market Intelligence` | `d5ef1458-c4f0-4dac-8de8-3118ab95fbb2` | news_events, signal_matches, get_client_signals |

Recipe (per desk): `POST /api/2.1/tag-policies` (top-level `tag_key`/`description`/`values:[{name:true}]`)
→ `POST /api/2.0/domains` (needs `tag_key` + `display_name` + `owner_ids:[<int>]`) → `ALTER
TABLE/VIEW/FUNCTION … SET TAGS ('<tag_key>'='true')`. Reserved chars in tag_key: no `&` (use "and"),
`/` is the subdomain separator. Domains = Public Preview.

## Genie One (front door A) — no build, discovery only
**There is no API to register a space into Genie One.** Genie One auto-discovers every certified
space / metric view / KA the *user* can access (UC permissions), then ranks via the **Genie Ontology
+ OntoRank** (authority + relevance). The workshop's job was to make each desk's discovery signals
strong — done in earlier phases:
- Certified: gold tables/views + `exposure_kpis` metric view (authority signal).
- Rich Genie space **descriptions + instructions + sample questions** (top routing lever):
  Portfolio `01f1a7d4c80a1e6c935c8f5fdc77e543`, Market Intel `01f1a7d7670719e5b46a73d654d41bca`.
- Discover **domain tags** (subject-area context).
- **Grants/RLS** decide per-user discovery (chinese-wall).

**Set expectations (verified):** Genie One is GA but its **chat/routing is Public Preview**; ranking
is stochastic (~98% consistent). **Genie + KA composition in Genie One is Private Preview** (single
space, UI-only) — for reliable structured (Genie) + unstructured (KA) composition, use the
**Capital Markets Copilot** (front door B), which is GA and was validated live here.

To use Genie One on pbb-demo: enroll Genie One + its chat/routing preview, then a broad audience asks
NL and Genie One discovers the right desk's certified space. No code.

## MLflow tracing (S5) — auto
Every managed MAS/KA endpoint auto-logs MLflow traces to its own experiment (no AI Gateway on these
endpoint types). The Copilot's multi-hop route shows as a span tree: Copilot → desk agent → its tools.

# Build log — CM Data Products Workshop

Autonomous phased build on `pbb-demo` / `ec_demo_workspace`. Each phase verified + audited before
the next. Path B (code) executed live; Path A (Genie Code prompts) authored in `PROMPT_RUNBOOK.md`.

## Phase 0 — Data foundation ✅ (2026-09-03; generator added 2026-09-04)
Two notebooks: `data/00_verify_foundation.py` (verifies the seed exists — used for the pbb-demo build,
which reused the Bellwether `cibc_cm` seed) and **`data/01_generate_seed.py`** (self-contained,
deterministic **from-scratch generator** so a customer can recreate the world on their own workspace:
clients, instruments, prices, positions, trades, research_notes, filing_facts, news_events_tagged,
client_signal_matches — structured tables in pure PySpark, text tables via `ai_query`; parameterized
`catalog`/`schema_prefix`; hero preserved; hard-seeds the AC 75/50/25 fact). `ai_query` expressions +
notional math validated live; **full run executed against a throwaway `cmgen_test` prefix** — cells
1–8 (all structured + ai_query text) succeeded (clients 9, positions 94, research_notes 45,
filing_facts 73, news 20); the final signal-matches cell hit a `LATERAL VIEW … JOIN` ordering
`PARSE_SYNTAX_ERROR`, **fixed** (explode in a subquery) and re-validated (signal_matches 207 rows,
AC net-long WTI = 150, AC hedge_policy fact present). Throwaway schemas dropped; `cibc_cm` desks
untouched (the run used a separate prefix).

Verified the reused Bellwether CM seed on `cibc_cm_silver` (+ `cibc_cm_gold`). Counts: clients 9
(w/ coverage_officer), positions 124, trades 626, instruments 22, research_notes 45, filing_facts
387, filing_chunks 1132, news_events_tagged 45, client_signal_matches 139. Coverage officers:
Sofia Martins (AC/MG), David Chen (BCE/MFC/BAM), Priya Nair (SU/CNR/ABX/CVE). Hero confirmed: AC
net-long WTI 150 / HO 75. Notebook `data/00_verify_foundation.py`.

## Phase 1 — Desk 1 (Portfolio & Exposure) ✅ (2026-09-03)
Vertical slice, both surfaces; code path executed + validated live.
- **D1.1** `cm_portfolio_gold.positions` (124, ties silver) + `.clients` (9); both certified.
- **D1.2** `cm_portfolio_metrics.exposure_kpis` metric view; MEASURE() totals tie exactly
  (gross $10.179B, 124 positions, 9 clients); Energy leads $2.78B. Certified.
- **D1.3** `get_client_positions` (AC → 8 rows) + `compute_shock_pnl` (AC WTI −10% → −CAD 1,575,153).
- **D1.4** Genie space `01f1a7d4c80a1e6c935c8f5fdc77e543` — asked "gross notional by sector" →
  MEASURE() SQL, Energy $2.78B (ties D1.2).
- **D1.5** Managed MCP URLs documented (`/api/2.0/mcp/functions/…/cm_portfolio_gold`,
  `/api/2.0/mcp/genie/<id>`); live client list-check deferred (local `mcp` transport hung).
- **D1.6** **Portfolio Desk Agent** — supervisor `5e43b418-ea31-4d2c-8fd4-158638dab7d8`, endpoint
  `mas-5e43b418-endpoint`, 3 tools (genie_space + 2 uc_function). Validated live: hero question
  routed both tools in one turn, numbers matched D1.3/D1.1.

**Audit:** all assets certified where required; every measure/function tied to raw; hero holds
end-to-end. No governance masks yet (Phase 3). SDK API confirmed by introspection: `tool_type`
values include `supervisor_agent` (the Phase-4 supervisor-of-supervisors hook).

## Phase 2 — Desks 2 & 3 ✅ (2026-09-03)
**Desk 2 — Research & Filings:**
- D2.1 `cm_research_gold.research_docs` (45 docs, 9 clients, KA file-table contract, CDF, certified).
- D2.2 `get_filing_facts(p_client_id, p_fact_type)` — AC returns 54 facts / 17 hedge_policy.
- D2.3 Research KA `ka-a462749b-endpoint` (source 45/45 ingested, 0 failed).
- D2.6 **Research Desk Agent** `mas-ac2a8b1e-endpoint` (KA + get_filing_facts). Validated live: the
  get_filing_facts route returned AC's real **75%/50%/25%** jet-fuel hedge policy w/ source pages.
- **KA retrieval route: index still building** at phase close. Direct KA query returns HTTP 500
  "Vector index … is not ready" — confirmed async index build, NOT a content/wiring/routing defect
  (corpus verified correct, files ingested, MAS wired, function route works). Re-validate before P4.

**Desk 3 — Market Intelligence:**
- D3.1 `cm_market_gold.news_events` + `.signal_matches` (certified) + D3.3 `get_client_signals`.
- D3.2 Market Intel Genie space `01f1a7d7670719e5b46a73d654d41bca`.
- D3.6 **Market Intel Desk Agent** `mas-cb2e43fd-endpoint` (Genie + get_client_signals). Validated
  live: "which clients exposed to WTI news" → Genie route, bearish-dominant sentiment breakdown.
- Design note: Desk 3 leads Genie+function (no vector sync) to contrast Desk 2's KA; DIY-VS path = recipe R2.

**Audit:** all views/tables/metric certified; every function tied to raw; 2 of 3 desk agents fully
validated live; Desk-2 KA retrieval pending async index (function route proven). 3 desk MAS +
2 new Genie spaces live.

## Phase 2 addendum — Research KA index READY ✅ (2026-09-03)
KA source reached `KNOWLEDGE_SOURCE_STATE_UPDATED` (~25 min after create). Direct query returns
grounded content. Research Desk Agent `mas-ac2a8b1e-endpoint` re-validated: single question →
composes **KA** (analyst house view + desk recommendation) **and** `get_filing_facts` (AC 75/50/25
jet-fuel policy) in one turn. Desk 2 fully validated end-to-end.

## Phase 3 — Govern (ABAC masks + chinese-wall RLS) ✅ (2026-09-03)
Schema `cm_governance`. Two patterns, both live:
- **ABAC column mask** — `mask_rating` on `cm_portfolio_gold.clients.credit_rating` (native SET MASK
  on a table); shows `***` unless caller in `cm_privileged` (group absent = default-masked demo).
- **Chinese-wall RLS** — `coverage_acl` map + `coverage_wall(officer)` / `coverage_wall_client(client_id)`
  functions. Native `SET ROW FILTER` on tables (clients, research_docs); baked-in WHERE on views
  (positions, signal_matches — metric view + UC functions inherit it).
- **Proven live:** owner temporarily scoped to 'Sofia Martins' → clients, positions, research_docs,
  signal_matches ALL returned only AC.TO + MG.TO (Sofia's coverage) across the three desks; full
  access restored → 9 clients, metric view back to $10.179B/124/9 (no regression).

**Governance caveat (documented):** the KA vector index is a snapshot built at sync time and does
NOT enforce per-caller UC row filters. The chinese-wall holds on structured paths (Genie, UC
functions, positions/clients/signal_matches); a restricted user could still retrieve research text
for non-covered clients via the KA. Mitigation: sync the KA from a row-filtered source, or scope a
KA per coverage/desk. Not a blocker for the demo (owner = full access).

## Phase 4 — Federate (Copilot + domains + Genie One) ✅ (2026-09-03/04)
**Front door B — Capital Markets Copilot (supervisor-of-supervisors):** created
`mas-cdaed1d0-endpoint` (supervisor cdaed1d0-32a8-4fea-b201-8583289f0dd3); registered all 3 desk
MAS as `supervisor_agent` sub-agent tools. **SDK gap:** Tool dataclass (sdk 0.134) has no
supervisor_agent spec field → registered via raw REST `POST /api/2.1/supervisor-agents/{id}/tools`
body `{"tool_type":"supervisor_agent","supervisor_agent":{"supervisor_agent_id":"<id>"}}`.
**Validated live:** cross-desk question ("AC oil exposure + WTI −10% PnL AND house view on fuel
hedging") → routed Portfolio desk (−CAD 1.58M, ties D1.3) + Research desk (house view + rec) and
synthesized. Full 2-hop supervisor-of-supervisors works.

**Discover domains (data-product boundaries):** 3 domains built + assets tagged —
Portfolio `65bd9c6a…`, Research `a45eaf62…`, Market `d5ef1458…`. Recipe: tag-policies (2.1, top-level
fields) → domains (2.0, needs tag_key + owner_ids ints) → SET TAGS. Verified in table_tags.

**Front door A — Genie One:** no build (no registration API); the certified spaces + metric view +
domain tags + rich descriptions are the discovery signals (OntoRank). Documented enrollment +
the verified caveats (routing Public Preview; Genie+KA composition Private Preview → use Copilot).

**MLflow tracing (S5):** auto on every MAS/KA endpoint (own experiment). Audit: all federation
paths validated except Genie One live routing (no API; governance/metadata verified instead).

## Phase 5 — From-scratch recipe cards (R1–R5) ✅ (2026-09-04)
`recipes/` — R1 attach existing MCP → UC → agent; R2 vectorize my docs (KA file_table + VS); R3
tables → Genie agent; R4 function → agent tool; R5 share to org. Each distills a pattern proven live
in Phases 1–4, with Path A + Path B code and a validation check.

## Phase 6 — Package + hand off ✅ (2026-09-04)
README refreshed with live IDs + validated hero; `FACILITATOR.md` (agenda, persona-reveal script,
reset, honest talking points, reproduce-on-customer notes). Per-desk READMEs done.
**Optional polish — DONE:**
- **Attendee-lab HTML** `cm-desks-attendee.html` — self-contained hands-on lab, **restructured into
  parallel tracks**: Setup (Admin) · Desk A Portfolio (A1–A3) · Desk B Research (B1–B2) · Desk C
  Market (C1–C2) · Admin Integration (D1–D4). Each group follows only its track and records
  **hand-off IDs** (Genie space id + desk-agent `supervisor_agent_id`/endpoint); Admin pieces them
  together (cross-desk governance, domains, Copilot supervisor-of-supervisors, Genie One, reveal).
  Sticky track nav; desk tracks orange, Admin track teal. Browser-verified.
- **Two-tier architecture diagram** — inline theme-aware SVG in the lab (front doors → desk agents →
  governed gold, with governance band). Verified rendering.
- **Discover Pages** — `governance/pages.md` authors the 5 CM ontology pages (Gross Notional, Net
  Exposure, Coverage/Chinese Wall, House View, Adverse Media) with synonyms/definition/business-use/
  related-assets, mapped to domains. Programmatic create is a known dead-end (no public API; Beta
  write path fails) → **UI hand-author by Elmer** (content ready). Deck-ready standalone SVG export
  can be produced on request.

## BUILD COMPLETE (Phases 0–6 core)
3 desks × (data product + desk agent) + firm Copilot (supervisor-of-supervisors) + governance
(ABAC + chinese-wall) + domains + Genie One discovery signals + R1–R5 recipes. Validated live on
pbb-demo. Repo: elmer-cecilio_data/cibc-cm-desks-workshop.

## Live resource IDs (pbb-demo)
- Genie space (Portfolio): `01f1a7d4c80a1e6c935c8f5fdc77e543`
- Portfolio Desk Agent: `5e43b418-…`, endpoint `mas-5e43b418-endpoint`
- Warehouse: `cf771eb9a270a746`; venv with sdk>=0.133 at `/tmp/cm-venv`

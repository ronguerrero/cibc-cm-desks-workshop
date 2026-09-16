# PROMPT_RUNBOOK — CM Data Products Workshop (3 desks, dual path)

Each module carries **two authoring paths** — pick per team:
- **A (Genie Code):** paste the prompt into Genie Code (Agent Mode) in the workspace. Zero install.
- **B (Code/SDK):** run the notebook/SDK/REST equivalent. Repeatable, CI-friendly, version-controlled.

Placeholders: `<catalog>` (default `ec_demo_workspace`), `<schema_prefix>` (seed prefix, default
`cibc_cm`), `<warehouse_id>`. Every module ends with a **✓ Validation** check. Hero: oil ↓ → AC fuel hedge.

> **Prerequisites (services + previews):** see `FACILITATOR.md` → *Prerequisites* before you start —
> Unity Catalog, a serverless SQL warehouse, Foundation Model APIs (`databricks-claude-haiku-4-5`),
> Agent Bricks (Knowledge Assistant + Multi-Agent Supervisor), Genie / Genie One (+ its chat/routing
> Public Preview), Discover domains (Public Preview), and account groups for the rating mask.

> **Status:** built + validated live on pbb-demo (`ec_demo_workspace`; see `BUILD_LOG.md`), then
> **reproduced from scratch on a clean workspace** (fevm-fins-canada / `fins_canada_catalog`,
> 2026-09-04) — seed → 3 desks → governance → Copilot → domains → persona reveal all ran end-to-end.
> See PLAN.md §2a (verified routing model), §7 (public MCP), `dryrun_fevm/DISCREPANCY_LOG.md`.

## Driving Genie Code (Path A) — how to actually run these prompts
*Mechanics verified on the [[agent-moat-genie]] Genie Code dry-run on this same workspace
(`fevm-fins-canada`); the CM prompts reuse the identical surfaces/skills. The CM Path-A prompts here
were **not** separately dry-run — Path B (code) was. Expect minor prompt iteration.*

- **One Genie Code chat per module — start a fresh chat each time.** The prompts are fully-qualified,
  so a new chat keeps context small and avoids Genie Code's context filling up on the long modules.
  No correctness cost. (This is the "new session per asset" step from the agent-moat build.)
- **Don't tell it to "confirm" or "approve."** Genie Code plans and executes end-to-end, auto-approving
  its own reads/writes. Paste the prompt, glance at the plan, let it run.
- **Genie Code's tools are context-sensitive to the open surface — be on the right page before you paste:**
  - **Discover domains (S1):** keep **Discover** open in the main pane (*not* a dashboard canvas) —
    Genie Code spins up a notebook and calls the domains REST from there.
  - **Genie spaces (D1.4, D3.2):** author from the **Genie** surface.
  - **KA + desk agents + Copilot (D2.3, D1.6 / D2.6 / D3.6, S3):** Genie Code loads the built-in
    **`databricks-agent-bricks`** skill and builds them via the SDK from a notebook — it
    `%pip install --upgrade databricks-sdk` (needs ≥ 0.133). **Expect churn here** (verified P-A dry-run):
    the old SDK stays module-cached, so Genie Code retries several ways and often **falls back to the
    Databricks CLI** before it succeeds. Let it run — it self-recovers; don't nudge it (a mid-run nudge
    spawned a duplicate agent). Optionally pre-provision `databricks-sdk>=0.133` on the serverless env.
  - **Discover Pages (S4):** Beta — **hand-authored in the Discover UI**; no prompt/API path today.
- **It uses notebooks for REST calls** (domains, agents) — expected. It auto-loads the right skills
  (metric-views, AI/BI dashboards, agent-bricks), so those modules are already fast.

---

## Phase 0 — Shared seed (facilitator, once)

Run **`data/01_generate_seed.py`** — a self-contained, deterministic from-scratch generator (no
external files, no Volumes). Produces the silver/gold CM world all desks build on: clients (9
Canadian names + `coverage_officer`), instruments/prices/positions/trades, research_notes,
filing_facts, news_events_tagged, client_signal_matches. Structured tables in pure PySpark; text
tables via `ai_query`. Parameterized `catalog` + `schema_prefix` widgets — **the same two every desk
notebook takes**. Runs on **serverless**. (`data/00_verify_foundation.py` just checks an existing seed.)

- **A:** prompt Genie Code to run `data/01_generate_seed.py`, then verify row counts.
- **B:** `databricks jobs submit` the notebook on **serverless** with `base_parameters {catalog, schema_prefix}`.

✓ 9 clients, 94 positions, 45 research_notes, 73 filing_facts, 20 news, signal matches present.
Hero: AC net-long WTI (validated live on fevm-fins-canada 2026-09-04).

---

## Desk 1 — Portfolio & Exposure

### D1.1 — Gold view + certify
Build `<catalog>.cm_portfolio_gold.positions` (+ clients, trades) from silver; snake_case; drop any
PAN/PII; certify. **Say "set the `system.certification_status` tag to certified"** — a bare "certify"
led Genie Code to a custom `certified=true` tag that skips the real Certified badge / Genie One
authority signal (verified P-A dry-run).
- **A:** "Create a gold schema `cm_portfolio_gold` and a certified `positions` view from
  silver.positions joined to clients (name, ticker, sector, desk, book, coverage_officer)…"
- **B:** `CREATE VIEW … ` DDL notebook + `ALTER … SET TAGS('system.certification_status'='certified')`.

✓ Row counts tie to silver; cert tag present in `information_schema.table_tags`.

### D1.2 — Metric view (semantic layer)
`cm_portfolio_metrics.exposure_kpis` — dims (Client/Ticker/Sector/Desk/Book/Currency/Coverage
Officer), measures (Gross Notional CAD, Net Exposure CAD, Unrealized PnL, Position/Client Count).
Every dim/measure gets a **description** (feeds discovery — PLAN §2a).
- **A:** Genie Code loads `databricks-metric-views` skill; "Build a metric view … with these
  measures using MEASURE()…"
- **B:** `CREATE VIEW … WITH METRICS LANGUAGE YAML AS $$ … $$` (version 0.1).

✓ `MEASURE(\`Gross Notional CAD\`)` ties to raw aggregate; Energy > Airlines ranking sane.

### D1.3 — UC function tools
`get_client_positions(p_client_id)`, `compute_shock_pnl(p_client_id, p_instrument_id, p_shock_pct)`. Params `p_`-prefixed
(SQL-UDF column-shadow gotcha). **Specify the PnL economics explicitly** or Genie Code guesses a naïve
`net_qty × spot × shock%` and the hero comes out ~1000× too small (verified P-A dry-run): PnL impact (CAD)
= `net_qty × (spot_price × p_shock_pct/100) × contract_size × CAD_FX_rate` — join `instruments` for
`contract_size` + native currency.
- **A:** "Create a UC table function `get_client_positions`…"
- **B:** `CREATE OR REPLACE FUNCTION` DDL; re-GRANT EXECUTE after each replace.

✓ `SELECT * FROM …get_client_positions('CL-AC')` returns AC book.

### D1.4 — Genie space
"Portfolio & Exposure" grounded on the metric view + gold views. **Description + instructions +
sample questions authored deliberately** (the biggest routing lever — PLAN §2a).
- **A:** Genie Code builds it (serialized_space is iteration-heavy — see agent-moat M7 recipe).
- **B:** serialized_space proto (version 2; tables sorted by identifier; sample Qs separate).

✓ "Gross notional by sector" → MEASURE() SQL, numbers match D1.2.

### D1.5 — MCP server
**(a) Expose our own** — **managed MCP (GA)** gives you the endpoint for free, no build:
`https://<ws>/api/2.0/mcp/functions/<catalog>/cm_portfolio_gold/get_client_positions` and
`…/api/2.0/mcp/genie/<portfolio_space_id>`. **(b) Public market data** = official `alpha_vantage_mcp`
(free-tier key). OpenFIGI has no public MCP → wrap ours + expose via managed MCP if needed.
- **A/B:** call the managed-MCP URL from an agent via `databricks-mcp` `DatabricksMCPClient`; add
  `alpha_vantage_mcp` as an external stdio/remote client. (See recipe **R1** for the full pattern.)

✓ `DatabricksMCPClient(server_url=…/mcp/functions/…).list_tools()` lists `get_client_positions`.

### D1.6 — Desk Supervisor Agent (multi-tool → own MAS)
Compose this desk's tools into **"Portfolio Desk Agent"** — a shareable desk-level MAS. Tools:
Genie space (D1.4) + `get_client_positions` + `compute_shock_pnl` (D1.3).
- **A:** Genie Code via `databricks-agent-bricks` skill.
- **B:** `w.supervisor_agents.create_supervisor_agent` + `create_tool` (`genie_space` / `uc_function`).

✓ "PnL if WTI drops 10% for Air Canada" routes Genie→positions→pnl in one turn. Endpoint READY.

---

## Desk 2 — Research & Filings

### D2.1 — Research corpus + certify
`cm_research_gold.research_docs` (from silver research_notes; content + `_metadata` STRUCT + CDF on
= KA file-table contract) and `filing_facts` from the seed.
- **A:** "Generate a research-notes table via ai_query(claude-haiku)… KA-shaped…"
- **B:** CTAS + `ai_query('databricks-claude-haiku-4-5', …)`; enable CDF; certify.

✓ Notes reference tickers/hedge programmes; filings parsed (AC 75% jet-fuel policy fact present).

### D2.2 — UC function
`get_filing_facts(p_client_id, p_fact_type)` over filing_facts.
- **A/B:** as D1.3 pattern.

✓ `get_filing_facts('CL-AC','hedge_policy')` → 75% jet fuel.

### D2.3 — Knowledge Assistant (vectorized)
KA over `research_notes` + filings — **Delta table IS a valid `file_table` source, no Volume
staging** (needs SDK ≥ 0.133). Description authored for routing.
- **A:** Genie Code via `databricks-agent-bricks` skill.
- **B:** `w.knowledge_assistants.create_knowledge_assistant()` + `create_knowledge_source(
  KnowledgeSource(source_type="file_table", file_table=FileTableSpec(table_name=…, file_col="content")))`.

✓ "House view on Air Canada fuel hedging?" → grounded answer with citations.

### D2.4 — (optional) small Genie space over filing metadata
For structured filing lookups (issuer, filing type, date). Description authored for routing.

### D2.5 — MCP server
**(a)** managed MCP over `get_filing_facts` + the KA; **(b)** public **`sec-edgar-mcp`** (keyless,
`User-Agent` header) for live EDGAR filings/XBRL/insider forms. **License caveat:** that repo is
**AGPL-3.0** — for a bank prefer the MIT-licensed **`datakoot/filings-intel-mcp`** (keyless, remote
HTTP) instead. Verify repo + license at workshop time.
- **A:** register the KA + UC function as managed MCP via Genie Code.
- **B:** managed MCP config; add the public EDGAR MCP as an external client.

✓ EDGAR MCP returns AC's latest 40-F facts; managed MCP exposes the KA to an external agent.

### D2.6 — Desk Supervisor Agent (multi-tool → own MAS)
Compose into **"Research Desk Agent"** — tools: KA (D2.3) + `get_filing_facts` (D2.2) + optional
filings Genie (D2.4).
- **B:** `create_supervisor_agent` + `create_tool` (`knowledge_assistant` / `uc_function` / `genie_space`).

✓ "House view on AC fuel hedging + the exact policy per filing" → KA + get_filing_facts (75%).

---

## Desk 3 — Market Intelligence

### D3.1 — News + signals gold + certify
`cm_market_gold.news_events_tagged`, `client_signal_matches`.
- **A/B:** build from silver news; AI-tag sentiment/asset-class/entities via ai_query.

✓ OPEC events tag bearish + WTI; AC matches oil-bearish events (hero).

### D3.2 — News KA / Vector Search index
KA or raw VS index over news for adverse-media Q&A (shows the DIY-vectorize path vs Desk 2's
managed KA).
- **A:** Genie Code (agent-bricks or vector-search skill).
- **B:** VS index over news chunks (gte-large-en) or `w.knowledge_assistants`.

✓ "Adverse media on Suncor last 30 days?" → cited news.

### D3.3 — Signal-match UC function
`get_client_signals(p_client_id, p_lookback_days)`.

✓ Returns AC's oil-bearish signal matches.

### D3.4 — Chatbot front (Lakebase app) OR Genie One surface
Either a small Lakebase-backed chat app (agent-moat M14 pattern: async-poll, SP auth, fresh PG
cred/conn) or expose via Genie One. Shows the "chatbot vs Genie One" choice.

### D3.5 — MCP server
**(a)** managed MCP over `get_client_signals` + the news KA/VS; **(b)** public
**`market-research-mcp`** ("Scout", MIT, **zero API keys**) — 62 tools bundling GDELT news/events,
FRED, yfinance, sentiment. No dedicated public GDELT-only MCP exists (Scout wraps it); our own
pbb-demo GDELT MCP is the alternative.
- **A/B:** managed MCP over the UC objects; Scout as an external stdio client.

✓ Scout returns adverse-media/events for a client; managed MCP exposes the signal function.

> **Reproducibility note:** Scout (#3, zero-key) + `filings-intel-mcp` (MIT, keyless) let CIBC
> reproduce the public-MCP layer with **no paid keys and no copyleft** — the recommended default.

### D3.6 — Desk agent (boundary case: MAS or direct)
Market Intel has 2 tools (news KA/VS + `get_client_signals`). Per the hybrid rule (§PLAN topology),
2+ tools → build **"Market Intel Desk Agent"** (like D1.6/D2.6). If the desk is scoped to a **single**
asset (just the news KA), skip the MAS and register that KA **directly** in the overall Copilot —
this is the illustrative "single-asset → direct" path.

✓ Either the desk MAS answers a 2-tool question, or the lone KA is registered directly in S3.

---

## Shared Layer

### S1 — Discover domains (per desk = data-product boundary)
One domain per desk (Portfolio / Research / Market Intelligence); tag each desk's tables + metric
view + functions. Domain = governed tag (PubPrev).
- **A:** Genie Code spins a notebook to call `/api/2.1/tag-policies` + `/api/2.0/domains` + SET TAGS.
- **B:** `governance/build_domains.py` (tag policy → domain → `ALTER … SET TAGS`).

✓ 3 domains; assets tagged; visible in Discover.

### S2 — Governance: ABAC masks + chinese-wall RLS
Mask client PII/MNPI; RLS by `coverage_officer` (Sofia/David/Priya). Masks + RLS flow *through*
the agent.
- **B (recommended for precision):** `mask_email`/`mask_phone` + `ALTER COLUMN SET MASK` keyed on
  `is_account_group_member(...)`; RLS policy on `current_setting`/group.

✓ Two logins, same question → different governed data.

### S3 — Front doors + ontology routing capstone
The two front doors are complementary by design (verified routing model — PLAN §2a):

**Front door A — Genie One (rank-based discovery, no registration).**
There is **no API to register spaces**; Genie One **auto-discovers** every space/KA/metric view the
user can access (UC permissions), then ranks via the **Genie Ontology + OntoRank** (authority +
relevance, permissions-aware). So the workshop's job is **make each desk's ontology assets strong**,
not "wire" them in. Checklist (verified lever order):
1. Space **name + description** clearly name the desk's subject (top signal).
2. **Certify** the space's tables + metric view (authority boost).
3. **Discover domain** tags on all assets (filter + domain context).
4. Space **instructions** steer interpretation; **Pages** (S4) add glossary/synonyms to the Ontology.
5. **Grants/RLS** decide per-user discovery (a user only sees — and is routed to — what they can access).
- **A/B:** no build step — this is governance + metadata (done in D*.1/D*.2/D*.4 + S1/S2/S4).
- **Set expectations:** ranking is stochastic (~98% consistent), Genie One **chat/routing is Public
  Preview** (Genie One GA Jan 2026). Enroll Genie One + its chat/routing preview in your workspace before the workshop.

✓ Sign in as a coverage officer, ask a desk-shaped question in Genie One → it discovers + routes to
that desk's certified space; a different persona (different grants) gets a different candidate set.

**Front door B — Capital Markets Copilot (deterministic, rules-based, supervisor-of-supervisors).**
Per the **hybrid topology** (PLAN §topology): each multi-tool desk already shipped its own desk MAS
(D1.6/D2.6/D3.6). The Copilot registers **each desk MAS as a `supervisor_agent` sub-agent tool**
(by its `supervisor_agent_id`) — a supervisor-of-supervisors — plus any single-asset desk's KA/Genie directly.
- **B (SDK + REST):** `w.supervisor_agents.create_supervisor_agent`, then register each desk agent via
  **raw REST** `POST /api/2.1/supervisor-agents/<copilot_id>/tools` with
  `{"tool_type":"supervisor_agent","supervisor_agent":{"supervisor_agent_id":"<desk_sid>"}}` — as of
  databricks-sdk 0.135 the `Tool` dataclass has no `supervisor_agent` field, so the SDK `create_tool`
  can't build this one (**verified** on fevm-fins-canada). Single-tool desks use the SDK `create_tool`.
  Invoke via Responses API `POST /serving-endpoints/<copilot>/invocations {"input":[{role,content}]}`
  (warms ~30-60s; not `messages`).
- **A (Genie Code):** build the same via the `databricks-agent-bricks` skill.

✓ "My book's oil exposure and the house view" → Copilot routes to **Portfolio Desk Agent** +
**Research Desk Agent** (each fans out to its own tools) in one turn; masks/RLS from S2 flow through
every hop.

> **The honest CIBC story:** Genie One = broad, zero-build discovery ranked by the ontology you
> curate (not a hard route, no per-persona rule, Preview). Copilot/MAS = deterministic, rules-based,
> persona-aware. Build both; use each for what it's good at.

### S4 — Discover Pages (ontology glossary) *(Path B / UI — Beta)*
5+ CM concept Pages (Gross Notional, Net Exposure, Coverage/Chinese Wall, House View, Adverse
Media) — synonyms + definition + related assets. **No public API (Beta)** → hand-author in
Discover UI. Additive; strengthens routing synonyms.

### S5 — Observability
MLflow Tracing on the mas-/ka- endpoints (auto-logged; no AI Gateway on these endpoint types).

✓ Multi-desk routing visible as a span tree (supervisor → desk tool → sub-tool).

---

## Persona reveal (demo close)
Same question — "my book's oil exposure and what research says" — as **Sofia** (covers AC/MG) vs
**David** (covers BCE/MFC/BAM): different clients, different governed data, both through one front
door. Then show the MLflow trace of the route.

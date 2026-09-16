# Capital Markets Data Products Workshop — "Trading Floor Copilot"

**Status:** PLAN / draft (2026-09-03). Source of truth for the multi-desk, build-from-scratch
capital-markets workshop. Derives from [[cibc_bellwether_project]] (CM data model) and
[[cibc_agent_moat_genie]] (prompt-driven, zero-install build runbook).

**Workspace:** `pbb-demo` (`adb-7405609454961946.6.azuredatabricks.net`), catalog
`ec_demo_workspace`. Bellwether CM data + plumbing already live here — desks build their own
governed products on top of a pre-seeded world.

---

## 1. The idea

One firm, three **desks**. Each desk independently builds a *combination* of agent assets over
its own data — Genie space(s), Knowledge Assistant(s), UC functions/tools, metric views, Vector
Search indexes, and **its own MCP server**. Each desk works in isolation.

Once a desk's assets are **governed and certified as a data product**, they are **synced and
shared up** to a larger audience through **two front doors, both required**:

1. **Genie One** — org-wide natural-language front door; certified Genie spaces + metric views
   become discoverable to analysts with zero build.
2. **Multi-Agent Supervisor chatbot** ("Capital Markets Copilot") — registers each desk's Genie
   space, KA, functions, and MCP tools; routes across desks; persona-aware.

The workshop's spine: **build independently → govern into a data product → then sync + share up.**

**Agent topology — HYBRID (decided 2026-09-03).** Each desk with **2+ tools** composes them into
its **own desk-level Supervisor Agent (MAS)** — a self-contained, independently shareable desk
agent = the agent form of its data product. The org-wide **Capital Markets Copilot** is then a
**supervisor-of-supervisors**: it registers each desk MAS's serving endpoint as a
`serving_endpoint` sub-agent tool (validated tool_type in [[project_cibc_agent_moat_build]]). A
desk that ends up with a single asset (e.g. just one KA) skips its own MAS and registers that asset
directly in the Copilot. This matches "build your own, then federate up," keeps the overall agent
simple (3 sub-agents, not ~9 tools), and demos the supervisor-of-supervisors pattern. Cost: one
extra hop per desk — acceptable.

## 2. Two-tier architecture

```
TIER 2 — SHARED (consumers)          Genie One  +  Capital Markets Copilot (MAS)
                                              ▲              ▲
                                     certified │  registered │ tools + MCP
                        ┌─────────────────────┼──────────────┼─────────────────────┐
TIER 1 — DESKS          │  Portfolio &        │  Research &   │  Market              │
(independent producers) │  Exposure           │  Filings      │  Intelligence        │
                        │  ───────────        │  ──────────   │  ─────────────       │
                        │  metric view        │  KA (VS)      │  news KA / VS        │
                        │  Genie space        │  filing fns   │  signal fn           │
                        │  position/PnL fns   │  Genie (meta) │  chatbot / Genie One │
                        │  MCP server         │  MCP server   │  MCP server          │
                        └─────────────────────┴──────────────┴──────────────────────┘
GOVERNANCE (spans both) UC: certification · ABAC masks (MNPI/PII) · RLS chinese-wall · MLflow Tracing · Unity AI Gateway
DATA (seeded/generated) clients · positions · trades · prices · research notes · filings (public) · news/signals
```

## 2a. The ontology / discovery layer — how the front door knows what to pick

The customer's requirement: **Genie One (and the Copilot) should know *which* desk's Genie
space / KA to leverage first, ideally ranked by the user and the domain they work in.** That
"knowing" is not magic — it's driven by the metadata and semantic assets each desk publishes.
The workshop makes desks build those assets *on purpose* so routing is good, not accidental.

**Discovery signals a desk must produce (each strengthens routing/ranking):**

| Signal | Asset | What it does for the front door |
|---|---|---|
| **Semantic definitions** | **Metric views** (UC Metrics) — dims + measures with descriptions | Gives the router governed, named business concepts ("Gross Notional", "Net Exposure") to match a question against; certified numbers |
| **Domain boundary** | **Discover domain** (governed tag) per desk | Scopes assets to a desk/subject area; the lever for *domain-based* ranking — a user working in "Portfolio" domain gets that desk's assets weighted up |
| **Glossary / ontology** | **Discover Pages** — term, synonyms, definition, business use, related assets | Human + machine ontology: synonyms map a user's words → the right desk's assets; "related assets" links a concept to its Genie space / KA / function |
| **Space intent** | Genie space **description + instructions + sample questions** | The primary text the router embeds/matches against; the single biggest lever on "which space" |
| **Trust signal** | **Certification** (`certification_status=certified`) | Eligibility + preference — certified products surface first in Genie One |
| **Per-user relevance** | UC **grants + group membership + coverage-officer RLS** | A user only discovers what they can see; persona shapes both *what* is offered and *what data* comes back |

**Routing mechanism — VERIFIED (2026-09-03, internal docs).** Genie One routing is a **hybrid,
rank-based** flow, NOT a rule engine and NOT a registration list:
`UC-permissions filter → semantic/keyword/authority ranking (OntoRank) → LLM agent/tool selection
→ space invocation`. Two named concepts underpin it:
- **Genie Ontology** — a business-context map built from **UC Semantics** (metric views, Discover
  domains, Pages/glossary) plus inferred snippets from dashboards, queries, and Genie Agents. This
  is *literally* the ontology the customer intuited, and the assets in the table above are its
  inputs.
- **OntoRank** — a **permissions-aware ranking algorithm** scoring snippet authority + relevance
  and resolving conflicting definitions. Important nuance: **OntoRank ranks candidate sources/
  snippets, it does not hard-route the top-level space choice.** Curating the ontology improves
  *consistency*, it doesn't guarantee a rule.

**Consequences to design around (and to tell CIBC honestly):**
1. **No "register into Genie One" API.** Spaces are **auto-discovered via UC permissions.** You
   influence routing only through metadata quality + governance, not a config list. (Genie
   `CreateSpace`/`UpdateSpace` manage a space; they do NOT enroll it in the router.)
2. **Ranking is stochastic (~98% consistent), not deterministic.** Good for discovery, not for a
   guaranteed route.
3. **Per-user relevance is indirect** — via UC permissions/groups + domain context, not an explicit
   "this persona prefers this desk" setting.
4. **For deterministic, persona-aware routing → use the Supervisor Agent** (front door B), whose
   sub-agent routing rules you control explicitly. **This is why both front doors matter:** Genie
   One = broad rank-based discovery; Copilot/MAS = deterministic, rules-based federation.
5. **Status:** Genie One is **GA (Jan 2026)** but its **chat/routing is Public Preview** (left Beta
   Apr 2026) — enroll + set expectations accordingly.
6. **Cross-agent composition — VERIFIED, important.** Genie One typically **routes to ONE best
   agent per question.** It can do limited *multi-Genie-space* text-level synthesis (separate
   queries merged in prose, no cross-space SQL join), but **Genie space + Knowledge Assistant in
   one answer is PRIVATE PREVIEW** — single-space, **UI-only (no API)**, enrollment reportedly
   closed ~late June 2026, fragile (documented failures), no GA ETA. → **For any question needing
   structured (Genie) + unstructured (KA) composed reliably, use the Supervisor Agent** (GA;
   explicitly supports Genie Agents + KA endpoints as sub-agents). This is the core reason the
   Copilot/MAS is the workhorse for composition and Genie One is the discovery/route-to-one layer.
   (Sources: "[External] Genie + Knowledge Assistant Integration Private Preview"; "OneChat Routing
   vs Orchestration Architecture"; "Use Supervisor Agent…" docs.) **Do NOT tell CIBC Genie One
   composes Genie+KA in production.**

**Highest-leverage levers (verified order):** (1) space **name + description**, (2) **certification**
(authority boost), (3) **UC permissions + domain tags** (filter + context), (4) space
**instructions**, (5) sample questions (mostly within-space answer quality, minimal cross-space
routing effect). Metric views and Pages feed the Ontology; UC Metrics contribution is inferred.

**So the "extra assets" the customer intuited are exactly right** — metric views (semantics),
Discover domains (boundary + context), Pages (ontology/glossary), rich space descriptions +
instructions (the top routing signal), certification (authority), and grants/RLS (per-user
relevance). Every desk builds all of them to become a shareable data product — that is what makes
Genie One rank it well and lets the Copilot route to it deterministically.

## 2b. Two build paths — pick per user/team

Same end state, two authoring surfaces. The runbook documents **both** side by side so a team
can choose; each module carries a Genie-Code prompt *and* the equivalent code/SDK snippet.

- **Path A — Genie Code prompting (zero install).** Drive everything from natural-language
  prompts in the workspace: data → metric view → certify → masks → UC functions → Genie space →
  KA → MAS → dashboard → Discover domain → (Lakebase app). Proven end-to-end in
  [[cibc_agent_moat_genie]]. Best for analysts / less-code teams; nothing to install.
- **Path B — Code / SDK (repeatable, CI-friendly).** Notebooks + Databricks SDK + REST + DABs:
  `w.knowledge_assistants`, `w.supervisor_agents`, `/api/2.1/tag-policies`, `/api/2.0/domains`,
  metric-view DDL, Genie serialized_space, Lakebase `w.database`/`w.postgres`. Proven in the SDK
  sibling [[project_cibc_agent_moat_build]]. Best for platform/eng teams who want it in a repo,
  reproducible across environments, under version control.
- **Parity note:** Genie Code can now build almost the whole stack incl. KA + MAS via the
  `databricks-agent-bricks` skill (verified 2026-09-02). Known gaps → Path B: **Discover Pages**
  (no public API yet; Beta GraphQL/UI only) and anything needing precise CI/idempotency. MCP
  server publishing is documented in both paths.

## 3. The three desks

Each desk = a **data product**: a mix of assets + a public data hook + its own MCP server.
Hero thread stays Bellwether's: **oil drops → Air Canada fuel-hedge implications.**

### Desk 1 — Portfolio & Exposure (structured / quant)
- **Data:** clients/issuers, positions (sector/desk/book dims), trades, 2yr prices.
- **Builds:** metric view (`portfolio_exposure_metrics` — exposure by sector/desk/currency) ·
  Genie space · UC functions (`get_client_positions`, `compute_shock_pnl`) ·
  **MCP server** (managed MCP over its UC functions + Genie space).
- **Public hook:** OpenFIGI (public instrument-identifier mapping) to resolve tickers; optional
  FRED (public rates/FX macro).
- **Sample Qs:** "Gross notional by sector"; "Which clients are net-long WTI?"; "PnL impact on
  Air Canada if WTI drops 10%?"

### Desk 2 — Research & Filings (unstructured / RAG)
- **Data:** analyst research notes (generated) + **real filing PDFs (public, SEC EDGAR / IR).**
- **Builds:** Knowledge Assistant over research + filings (vectorized, VS) · `get_filing_facts`
  UC function · small Genie space over filing metadata · **MCP server** (EDGAR MCP over public
  filings + managed MCP over its KA/function).
- **Public hook:** **SEC EDGAR** — fully public filings API; reproducible via download scripts.
- **Sample Qs:** "What's our house view on Air Canada's fuel hedging?"; "Air Canada jet-fuel
  hedge policy per the latest filing?" (→ 75% policy fact).

### Desk 3 — Market Intelligence (external signals)
- **Data:** news events + signal matches (generated), external adverse-media.
- **Builds:** news KA / Vector Search index · signal-matching UC function · a small chatbot app
  (Lakebase-backed) **or** a Genie One surface · **MCP server** (GDELT adverse-media MCP).
- **Public hook:** **GDELT** — public global news/events; already wrapped as an MCP on pbb-demo.
- **Sample Qs:** "Which clients are exposed to the latest OPEC headline?"; "Adverse media on
  Suncor in the last 30 days?"

## 4. Data seed + generation (reproducible — required)

CIBC may ask to duplicate this in their own environment, so **everything is generated / public**,
no hand-loaded internal data. Reuse Bellwether's generators (all dependency-free, `<catalog>`
placeholder):

| Layer | Source | Reuse from |
|---|---|---|
| Clients / positions / trades / prices | synthetic generator (PySpark + NumPy) | Bellwether `pipelines/01_seed_data.py` |
| Research notes | `ai_query` (Claude Haiku) → keyword-rich notes | Bellwether 2.0 "P21" recipe |
| Filings PDFs | **public** SEC EDGAR + IR CDN download | Bellwether 2.0 sourcing method (documented) |
| News + signal matches | news ingest + AI tagging (`ai_query`) | Bellwether `pipelines/02_news_ingest` |
| `coverage_officer` (chinese-wall RLS) | assigned in generator | Bellwether 2.0 (Sofia / David / Priya) |

Package these into the workshop repo with a `<catalog>` placeholder so a desk can regenerate its
own slice on any workspace. Roster = the 9 validated Canadian CM names.

**BUILT: `data/01_generate_seed.py`** — a single self-contained, deterministic generator (no
external files/Volumes) parameterized by `catalog`/`schema_prefix`, producing all silver+gold tables
the desks need (structured in PySpark; research_notes/filing_facts/news via `ai_query`); hero
preserved and the AC 75/50/25 fact hard-seeded. This is the customer's recreate-from-scratch entry
point. The **real public-filings** upgrade (SEC EDGAR PDFs → `ai_parse_document`) is optional and
lives in recipe R2 / the Bellwether 2.0 corpus pipeline for teams that want genuine filing text
instead of synthesized facts.

## 5. Governance = the "data product" gate

A desk is not shareable until its bundle is governed:
- **Discover domain** (a governed tag) wraps the desk's tables + metric view + Genie + KA +
  functions → the data-product boundary and catalog entry. (Domains = Public Preview; enabled on
  pbb-demo.)
- **Certification** (`system.certification_status=certified`) → also the eligibility signal for
  Genie One surfacing.
- **ABAC masks** (MNPI, client PII) + **RLS chinese-wall by coverage officer** → travel with the
  assets, enforced identically in both front doors. Masks flow *through* the agent (proven in
  agent-moat: Genie-sourced answers stay masked).

## 6. Sync + share — both front doors

- **Genie One (front door A):** certified desk Genie spaces + metric views become discoverable;
  broad audience asks NL, Genie One reaches the right product. Zero build for consumers. Genie One
  consumer access is GA on Azure.
- **Capital Markets Copilot / MAS (front door B):** Agent Bricks Supervisor registers each desk's
  Genie space + KA + UC functions as tools (Bellwether-supervisor pattern, already live). Routes
  across desks; persona-aware.
- **MCP (the "share a tool, not just data" layer):** each desk publishes an MCP server —
  Databricks *managed* MCP (UC functions / Genie / VS exposed as MCP) and/or a *custom* MCP app
  wrapping a public API (GDELT, OpenFIGI, EDGAR — all already built on pbb-demo). Makes a desk's
  product consumable by the Copilot, another desk, or an external client (e.g. Claude) — governed
  the same way.
- *(Cross-workspace/BU sharing, if ever in scope, = **Delta Sharing** of the underlying data
  product. Out of scope unless requested.)*

## 7. Public data / MCP candidates (researched 2026-09-03)

Two layers per desk: **(a)** Databricks *managed* MCP over the desk's own UC functions / Genie /
VS (no external dep, governed) — always available; **(b)** a *public* external MCP for the public
data hook. Best verified public options (git clone + pip, <5 min):

| Desk | Public MCP | Data | Auth | Maintainer | Caveat |
|---|---|---|---|---|---|
| **2 Research** | **`sec-edgar-mcp`** (stefanoamorelli) — 10-K/40-F, XBRL, insider Forms 3/4/5 | SEC EDGAR | keyless (`User-Agent` header) | community, ~355★ | **AGPL-3.0** — copyleft; flag for a bank. Alt: `datakoot/filings-intel-mcp` (MIT, keyless, remote HTTP) |
| **1 Portfolio** | **`alpha_vantage_mcp`** — stocks/options/technicals/macro/FX | Alpha Vantage | free tier key (paid for volume) | **OFFICIAL** (Alpha Vantage), MIT | free-tier rate limits; OpenFIGI has **no public MCP** → managed MCP over our own OpenFIGI wrapper |
| **3 Market Intel** | **`market-research-mcp`** ("Scout", pedrobraiti) — 62 tools incl. news/GDELT, FRED, yfinance, sentiment | yfinance/SEC/FRED/GDELT/CoinGecko | **none** | community, MIT | small project; all-free, zero-key = strongest reproducibility |
| macro (opt) | **`openecon-data`** (hanlulong) — FRED/World Bank/IMF/Eurostat NL router | 11 macro sources | OpenRouter key (LLM) | community | needs an LLM key |

**Not found (confirmed):** no dedicated public **GDELT-only** MCP (Scout wraps GDELT), no public
**OpenFIGI** MCP, no Anthropic-curated financial MCP registry. For GDELT/OpenFIGI, either reuse our
own pbb-demo MCP servers or expose via Databricks managed MCP.

**Reproducibility pick for CIBC:** lead with **Scout (#3, zero-key)** + **sec-edgar-mcp (#2,
keyless)** so a customer reproduces with no paid keys; add official **alpha_vantage_mcp** only if
live market data is wanted. **TODO:** verify each repo + license currency at workshop time (AGPL on
the EDGAR one is the one real blocker for a bank — prefer the MIT `filings-intel-mcp` alternative).

## 8. Build surface

- **Prompt-driven, zero install** via **Genie Code** for data → metric view → certification →
  masks → UC functions → Genie space → KA → MAS → dashboard → Lakebase app (the
  `cibc-agent-moat-genie` PROMPT_RUNBOOK proves all of this on samples data; this is a CM reskin).
- **GA:** Genie spaces, metric views, KA, Supervisor Agent, Vector Search, managed MCP, MLflow
  Tracing, Genie One (Azure). **Preview:** Discover Domains (PubPrev) / Pages (Beta).
- CIBC clearance: no CSP, cross-geo US already on → Genie Code Agent Mode is unblocked.

## 9. Agenda

**Half-day (core, ~4h):**
1. Parallel desk build (~2.5h) — each desk builds its combo from prompts, independently.
2. Govern → data product (~40m) — certify, ABAC/RLS, Discover domain.
3. Sync + share (~40m) — surface certified products into Genie One + register into the Copilot;
   publish MCP endpoints.
4. Persona reveal (~30m) — same question, two logins (Sofia vs David) → different governed
   answers; MLflow traces show multi-desk routing.

**Full-day (+4h):** deeper governance (MNPI classification, Discover Pages), a custom Lakebase
memory chatbot as the MAS front end, per-desk MCP consumed by an external Claude client, and a
"reproduce on your workspace" hands-on using the generators.

## 10. Reuse vs. build-new

- **Reuse (pbb-demo):** `cibc_cm_*` schemas (raw→gold), metric view `portfolio_exposure_metrics`,
  Genie space `01f14a4155b313ecad26a101e1b766d1`, `bellwether-vs` + `filings_idx`/`news_idx`,
  `bellwether-supervisor` endpoint, `bellwether-lakebase` pgvector, GDELT/OpenFIGI/compliance MCP
  servers, coverage_officer RLS, Bellwether generators.
- **Build new:** the **multi-desk framing** (3 parallel data products), a **CM reskin of the
  PROMPT_RUNBOOK** (desk-scoped prompt tracks), **per-desk MCP** publishing, the **dual front-door
  federation** step, and packaging the generators for CIBC self-reproduction.

## 11. Packaging for hand-off (reproducible)

Deliver a repo (`<catalog>` placeholder, no internal data/IDs — like
`agent-moat-attendee-standalone.html`):
- Data generators + public-data download scripts (EDGAR/GDELT/OpenFIGI).
- `PROMPT_RUNBOOK.md` — desk-scoped Genie Code prompts, each with a validation check.
- **Runnable notebooks (Path B)** — see §11a; one per desk build step, executable end-to-end.
- **From-scratch recipe cards** — see §11b; keyed to what a customer says ("I have an MCP
  server…", "here are my docs to vectorize…").
- Attendee-lab HTML (hands-on, copy-paste prompts, fonts embedded, zero external calls).
- Facilitator guide (agenda, persona logins, reset scripts).
- Governance recipes (certify, ABAC/RLS, Discover domain).

## 11a. Two build surfaces, split by desk

The workshop must show **both** how it's built in code (notebooks, for platform/eng teams) **and**
via Genie Code prompts (for analysts). Rather than double every module, each desk **leads** with
one surface and the runbook keeps the other as the alternate path — so the room sees both surfaces
demoed live, and every team has a complete path for the surface they prefer.

**Proposed lead split (adjust to audience):**
| Desk | Lead surface | Why | Alternate path still documented |
|---|---|---|---|
| **1 Portfolio & Exposure** | **Code notebooks (Path B)** | Quant/eng audience; metric-view DDL, UC fns, MAS SDK are cleanest in code + version control | Genie Code prompts |
| **2 Research & Filings** | **Genie Code (Path A)** | KA + "vectorize my docs" is the flagship zero-install prompt story | Notebook (SDK `w.knowledge_assistants`) |
| **3 Market Intelligence** | **Either / mixed** | Shows public MCP attach (code) + a Genie-One-vs-chatbot choice | both |

Every desk still delivers **both** artifacts (a notebook set + a prompt set); the "lead" only sets
what's demoed live in that desk's slot. Notebooks are the real, executable Path B — not pseudocode:
`data/`, `metric_views/`, `functions/`, `agents/` (KA + MAS via SDK ≥0.133), `governance/`,
`mcp/`, each runnable on the seeded data with a validation cell.

> **Update (2026-09-04):** the **attendee lab now shows _both_ surfaces inline on every step** —
> a Genie Code prompt (Path A) and a collapsible Path-B code block — so each group picks its surface
> per step rather than being assigned a lead. The lead-split above is now just the facilitator's
> choice of *what to demo live* in each desk's slot, not a constraint on the attendee.

## 11b. "From scratch" recipe cards (keyed to customer asks)

Standalone, copy-pasteable recipes for the real questions a customer brings — each as a short
notebook + a Genie Code prompt, independent of the desk narrative:

- **R1 — "I already run an MCP server. How do I attach it to UC and my agent?"** *(mechanics
  VERIFIED 2026-09-03; confirm exact SDK signatures against the installed SDK at build time.)*
  Three MCP shapes on Databricks — the recipe branches on which the customer has:
  - **(a) External/third-party MCP they run elsewhere** (their case) → register in UC as an **HTTP
    Connection + "MCP Service" wrapper**. **Public Preview** (Jan 2026). **No SQL DDL** — use REST
    `POST /api/2.1/unity-catalog/mcp-services` (`parent=schemas/<cat>.<schema>`, `mcp_service_id`,
    `config.source_connection.name=connections/<cat>.<schema>.<conn>`) or the SDK
    `w.ai_gateway.create_mcp_service(...)`. Auth on the underlying connection: bearer token via
    `secret()`, OAuth M2M/U2M, or Dynamic Client Registration. Governed like any UC object.
  - **(b) Managed MCP** (GA) — Databricks *hosts* an MCP over your own UC functions / Genie / AI
    Search / SQL at `https://<ws>/api/2.0/mcp/{path}` (`/mcp/functions/<cat>/<schema>/<fn>`,
    `/mcp/genie/<space_id>`, `/mcp/ai-search/<cat>/<schema>/<index>`, `/mcp/sql`). This is the "make
    MY stuff an MCP" path each desk uses in D*.5.
  - **(c) Custom MCP as a Databricks App** (GA) — deploy their server as an App, endpoint `/mcp`.
  - **Attach to an agent:** Supervisor → point a tool at the **MCP Service URL**
    (`https://<ws>/ai-gateway/mcp-services/<cat>.<schema>.<id>`; no explicit `tool_type="mcp"`
    confirmed — verify at build). Custom Mosaic AI agent → `pip install databricks-mcp`, then
    `DatabricksMCPClient(server_url=..., workspace_client=WorkspaceClient())` → `.list_tools()` /
    `.call_tool(name, args)`. This card ships as a notebook (register + attach + call) + a Genie
    Code prompt.
- **R2 — "Here are my documents. How do I vectorize them and query them?"**
  Two routes: **managed KA** (Delta table with `content` + `_metadata` STRUCT + CDF = file_table
  source, no Volume staging) and **raw Vector Search** (chunk → gte-large-en embed → DELTA_SYNC
  index → query). Both from a notebook and from a Genie Code prompt. Shows KA (easy) vs VS (DIY).
- **R3 — "I have tables. How do I make a Genie agent over them?"**
  gold view → metric view (semantics) → certify → Genie space with description/instructions/sample
  Qs. (= desk D*.1/.2/.4 distilled into one card.)
- **R4 — "I have a SQL/Python function. How do I make it an agent tool?"**
  UC function (`p_`-prefixed params) → grant EXECUTE → register as MAS `uc_function` tool / managed
  MCP.
- **R5 — "How do I share my product to the org?"**
  Certify + Discover domain + (Pages) → discoverable in Genie One; register into the Copilot MAS.
  Includes the honest routing caveat (§2a).

Each card = **notebook + prompt + ✓ validation**, so a customer can lift the one that matches their
starting point without running the whole workshop.

## 13. Build sequence (execution plan)

Principle: **build one desk as a vertical slice first, validate it end-to-end, then replicate.**
De-risks the pattern before we spend effort ×3. Each phase ends with a live ✓ validation on
pbb-demo (like the agent-moat-genie dry-runs). Reuse Bellwether assets where they exist.

**Phase 0 — Data foundation (gate).** Seed/verify the CM world on pbb-demo: clients (9 +
coverage_officer), positions/trades/prices, research notes, public filings corpus, news+signals.
Reuse Bellwether generators; package them with `<catalog>` placeholder for reproduction.
→ ✓ row counts + hero (AC net-long WTI) confirmed. *(Fork: fresh seed vs build on existing
Bellwether raw/silver — see §12.)*

**Phase 1 — Desk 1 (Portfolio) as the reference vertical slice, BOTH surfaces.** Build
D1.1→D1.6 to a live desk MAS: gold+certify → metric view → UC functions → Genie space → managed
MCP → **Portfolio Desk Agent**. Author the **Path-B notebook set** here (it becomes the template
for the other desks' notebooks) AND the Path-A prompts. This is the deepest single thread.
→ ✓ "PnL if WTI drops 10% for AC" routes end-to-end through the desk MAS.

**Phase 2 — Desk 2 (Research, Genie-Code-led) + Desk 3 (Market Intel, mixed).** Replicate the
proven pattern: KA over docs/filings + filing function (+ EDGAR MCP) → **Research Desk Agent**;
news KA/VS + signal function (+ Scout MCP) → **Market Intel Desk Agent** (or single-asset direct).
→ ✓ each desk MAS answers its hero question with citations.

**Phase 3 — Govern into data products.** Certify all desk assets; ABAC masks (PII/MNPI) + RLS
chinese-wall by coverage_officer; one Discover domain per desk. (S1–S2, + S4 Pages hand-authored.)
→ ✓ two logins (Sofia vs David), same question → different governed data.

**Phase 4 — Federate (both front doors).** **Copilot = supervisor-of-supervisors** registering the
3 desk MAS endpoints (S3-B). **Genie One** = ensure certified assets + domains + descriptions so
auto-discovery ranks them (S3-A; no build, governance only). MLflow tracing on (S5).
→ ✓ cross-desk question routes through desk agents in one turn; Genie One discovers the right desk.

**Phase 5 — From-scratch recipe cards (R1–R5).** Standalone notebook + prompt + ✓ each, lifted from
the desk builds: attach-existing-MCP, vectorize-my-docs, tables→Genie, function→tool, share-to-org.

**Phase 6 — Package + hand off.** Attendee-lab HTML (fonts embedded, zero external calls),
facilitator guide (agenda, persona logins, reset scripts), generators + public-data download
scripts, two-tier + routing diagram. Push private GitHub repo. Dry-run the full flow once.

**Critical path:** Phase 0 → 1 gate everything. Phases 5–6 can start once Phase 1 exists (recipes
are distilled from Desk 1). Governance (3) must precede federation (4). Genie One work is
governance-only, so it rides along with Phase 3.

**Effort read (rough):** P0 ~0.5d (mostly reuse), P1 ~1.5–2d (template build), P2 ~1.5d, P3 ~1d,
P4 ~1d, P5 ~1d, P6 ~1d. ~7–8 build-days worst case; stop-anytime-usable after each phase.

## 12. Open items / next steps

- [x] Curate public financial MCP options — §7 done (Scout / sec-edgar / alpha_vantage / openecon).
- [x] Draft the **CM-reskinned PROMPT_RUNBOOK** (3 desk tracks, dual path) — `PROMPT_RUNBOOK.md`.
- [x] Fill **S3 routing capstone + §2a mechanism** — Genie One routing model VERIFIED + documented.
- [x] Fill **R1 recipe (attach existing MCP → UC → agent)** — VERIFIED mechanics in §11b.
- [ ] Build the **Path-B notebook sets** per desk (§11a) + the **R1–R5 recipe cards** (§11b).
- [ ] Confirm the **desk lead-surface split** (§11a) with Elmer.
- [ ] Verify each public MCP repo + license at workshop time (AGPL on sec-edgar-mcp = bank blocker).
- [ ] Decide half-day vs full-day for the first run.
- [ ] Confirm Genie One + **its chat/routing Public Preview** enrolled on pbb-demo before the workshop.
- [ ] Dry-run 1–2 runbook modules in-workspace to tighten prompts (like agent-moat-genie dry-runs).
- [ ] Seed/verify the CM data products on pbb-demo (or regenerate cleanly from the generators).
- [ ] Render the two-tier architecture as a diagram for the deck/attendee lab.

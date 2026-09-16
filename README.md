# CM Data Products Workshop — "Trading Floor Copilot"

A multi-desk, build-from-scratch **capital markets** workshop on Databricks: several trading-floor
**desks** each independently build their own agent stack (Genie space, Knowledge Assistant, UC
functions/tools, metric view, Vector Search, and their own MCP server), govern it into a **data
product**, then federate up to a bigger audience through **two front doors** — **Genie One**
(broad, rank-based discovery) and a **Capital Markets Copilot** (a Multi-Agent Supervisor for
deterministic, persona-aware composition).

Shows **both build surfaces** — runnable **code notebooks** and **Genie Code** prompts — and
**from-scratch recipe cards** keyed to what a customer actually asks ("I have an MCP server, how do
I attach it to UC and my agent?", "here are my documents to vectorize").

## Contents

- **`PLAN.md`** — source of truth: two-tier architecture, the ontology/discovery layer, the
  verified Genie One routing model, public-MCP options, dual build path, hybrid agent topology,
  deliverables, and the phased build sequence (§13).
- **`PROMPT_RUNBOOK.md`** — 3 desk tracks + shared layer; every module carries an **A (Genie Code
  prompt)** and **B (code/SDK)** path plus a ✓ validation check.

## Prerequisites (services + previews)

Full checklist in **`FACILITATOR.md` → Prerequisites**. In short, the workspace needs: **Unity
Catalog** + a writable catalog; a **serverless SQL warehouse** (+ serverless notebooks/jobs);
**Foundation Model APIs** with `databricks-claude-haiku-4-5` served (the seed's `ai_query`) and AI
features enabled; **Agent Bricks** — Knowledge Assistant + Multi-Agent Supervisor (Path B needs
**databricks-sdk ≥ 0.133**); **Genie** + **Genie One** (its chat/routing is **Public Preview** —
enroll); **Discover domains** (**Public Preview**); **metric views**, **ABAC**, and **managed MCP**
(GA); and **account groups** `cm_privileged` / `cm_all_access` for the rating mask (account admin).

## Key facts (verified)

- **Genie One routing** is rank-based (OntoRank over UC Semantics), **not** rule-based, with **no
  "register a space" API** — you influence it via metadata + governance. Chat/routing is Public
  Preview.
- **Genie + Knowledge Assistant composition in Genie One is Private Preview** (single-space,
  UI-only, fragile) — for reliable structured+unstructured composition, use the **Supervisor Agent
  (GA)**.
- **MCP on Databricks:** managed MCP (GA) exposes UC funcs/Genie/VS at `/api/2.0/mcp/...`; custom
  MCP as Databricks Apps (GA); **external MCP registers into UC as an HTTP Connection + MCP Service
  wrapper (Public Preview, REST/SDK — no SQL DDL)**.

## Status — BUILT & VALIDATED LIVE on pbb-demo, REPRODUCED on a clean workspace (2026-09-04)

Phases 0–5 built and validated end-to-end on pbb-demo (see `BUILD_LOG.md`), then **reproduced from
scratch on a clean, different-cloud workspace** (fevm-fins-canada / `fins_canada_catalog`) to prove
portability — seed → 3 desks → governance → Copilot → domains → persona reveal all ran end-to-end;
findings folded back into the guides (`dryrun_fevm/DISCREPANCY_LOG.md`). 3 desks → 3 desk agents → 1
firm-wide Copilot (supervisor-of-supervisors), governed by ABAC masks + chinese-wall RLS, with
Discover domains and Genie-One-ready discovery signals.

### Live resources (`ec_demo_workspace`)
| Desk | Genie space | Desk Agent (MAS) | KA |
|---|---|---|---|
| Portfolio & Exposure | `01f1a7d4c80a1e6c935c8f5fdc77e543` | `mas-5e43b418-endpoint` | — |
| Research & Filings | — | `mas-ac2a8b1e-endpoint` | `ka-a462749b-endpoint` |
| Market Intelligence | `01f1a7d7670719e5b46a73d654d41bca` | `mas-cb2e43fd-endpoint` | — |
| **Capital Markets Copilot** | | **`mas-cdaed1d0-endpoint`** (routes all 3 desks) | |

Schemas: `cm_portfolio_gold` / `cm_portfolio_metrics`, `cm_research_gold`, `cm_market_gold`,
`cm_governance`. Domains: `CM Portfolio and Exposure`, `CM Research and Filings`, `CM Market Intelligence`.

### Hero validated
"For Air Canada: oil exposure + PnL if WTI drops 10%, and the house view on fuel hedging" → the
Copilot routes Portfolio desk (**≈ −CAD 1.6M**) + Research desk (75/50/25 hedge policy + house view),
synthesized in one answer. Chinese-wall: scope a user to one coverage officer → they see only their
clients across all desks.

### Reproduce on your own workspace
Run **`data/01_generate_seed.py`** with your `catalog` + a fresh `schema_prefix` — a self-contained,
deterministic generator (no external files) that builds the entire capital-markets seed from scratch
(structured tables in PySpark; research/filings/news via `ai_query`). Then run each desk's notebooks
**with the same two widgets** (`catalog`, `schema_prefix`) — they read the seed you generated. The
Genie-space builders take `--warehouse-id`; the agent / KA / Copilot scripts take `--profile` and the
IDs the prior steps hand off (Genie space id, KA id/endpoint, desk `supervisor_agent_id`s). Desk
*product* schemas (`cm_portfolio_gold`, etc.) are fixed names. Everything is generated or public — no
internal data. `data/00_verify_foundation.py` just checks a seed already exists.

**From-scratch reproduction dry-run — verified 2026-09-04 on `fevm-fins-canada` / `fins_canada_catalog`**
(a clean AWS workspace, different from the pbb-demo Azure build): seed → all 3 desks → governance →
Copilot → domains → persona reveal all ran end-to-end. The chinese-wall was confirmed to follow
**through the desk agents** (OBO): a caller scoped to one officer sees their client via the agent but
not others'. RNG-driven aggregates are seed-dependent (e.g. Energy gross notional ≈ CAD 1.6B on the
generator seed, vs the Bellwether-derived 2.78B); the hard-seeded hero (AC WTI/HO, −CAD 1.6M shock,
75/50/25 policy) reproduces exactly. See `dryrun_fevm/DISCREPANCY_LOG.md`.

### Layout
`data/` (`01_generate_seed` from-scratch generator + `00_verify_foundation`) · `desk1_portfolio/` `desk2_research/` `desk3_market/` (per-desk notebooks
+ MCP notes + README) · `governance/` (ABAC + RLS) · `federation/` (Copilot + domains + Genie One) ·
`recipes/` (R1–R5 from-scratch cards) · `tools/` (agent invoke helper) · `PLAN.md` `PROMPT_RUNBOOK.md`
`BUILD_LOG.md` `FACILITATOR.md`.

**Polish done:** `cm-desks-attendee.html` (hands-on lab + two-tier architecture SVG, browser-verified);
`governance/pages.md` (5 Discover Pages content, ready to hand-author in the UI — no public API).
Only genuinely pending item is publishing those 5 Pages in the Discover UI (Beta; content is ready).

## Lineage

Derives from the Bellwether CM data model and the agent-moat-genie prompt-driven runbook.
Workspace: `pbb-demo`, catalog `ec_demo_workspace`.

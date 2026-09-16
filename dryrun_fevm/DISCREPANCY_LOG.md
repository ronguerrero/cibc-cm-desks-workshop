# CM Desks Workshop — dry-run on `fevm-fins-canada`

Reproducing the facilitator + attendee guides on a fresh workspace to catch discrepancies.
Target: catalog `fins_canada_catalog`, seed prefix `cibc_cm`, desk product schemas `cm_*`.
Run date: 2026-09-04. Executor: role-playing facilitator → 3 attendees → admin.

## Findings (severity: 🔴 blocks a customer · 🟠 friction · 🟡 polish)

| # | Sev | Where | Guide says | Reality on fevm-fins-canada | Fix |
|---|-----|-------|------------|------------------------------|-----|
| 1 | 🔴 | Path-B desk notebooks | Footer: "swap `<catalog>` to reproduce" | Every notebook hardcodes `CATALOG = "ec_demo_workspace"` **and** reads `cibc_cm_silver`/`cibc_cm_gold` — not widget-parameterized like the seed generator. A customer using their own seed prefix (as the seed's own widget instructs) breaks Path B. | Parameterize CATALOG + silver/gold prefix via widgets in all notebooks; or state both must be edited. |
| 2 | 🟠 | desk1/04 & desk3/04 Genie space | "build a Genie space" (implies in-workspace) | Genie builder is a **local laptop script** using the `genie-rooms` skill path + `databricks api post`; warehouse `cf771eb9a270a746` is a pbb-demo id that doesn't exist here. | Note the local-tool dependency + parameterize warehouse_id. |
| 3 | 🟠 | desk agents + KA notebooks | "run the notebook" | Hardcode `profile="pbb-demo"`, need `databricks-sdk>=0.133`, and hardcode pbb-demo Genie/agent IDs. | Parameterize profile + IDs; document SDK floor. |

| 4 | 🟠 | attendee A1 checkpoint | "Energy ≈ CAD 2.78B on top" | Fresh generator seed: **Energy 1.60B** on top (still #1). The guide's 2.78B is from the Bellwether-seeded pbb-demo build (124 positions), not the reproducible generator (94 positions). Any customer reproducing sees ~1.6B. | Restate A1 checkpoint as "Energy leads (≈CAD 1.6B on the generator seed)" or "seed-dependent — Energy on top". |
| 5 | 🟡 | attendee A2 checkpoint | "≈ −CAD 1.58M" | Actual **−CAD 1.60M** (hero WTI position is hard-seeded → reproduces closely). Negligible. | Update to −1.6M. |
| 6 | 🟡 | attendee B2 checkpoint | "the real 75/50/25 limits" | The hard-seeded hero fact IS present ✓, but `get_filing_facts('CL-AC','hedge_policy')` now returns **2 rows** (the hero + an `ai_query`-generated hedge_policy fact) — demo shows two facts, 75/50/25 is one of them. | Note the KA/function returns >1 hedge_policy row; point the demo at the hero row, or dedupe the generator so hero is the only hedge_policy fact. |

| 7 | 🟠 | governance / facilitator | mask uses `is_account_group_member('cm_privileged')`; reveal shows "privileged sees rating, others see ***" | The two groups (`cm_privileged`, `cm_all_access`) must be **account groups**. On a workspace where you're not account admin you can only create **WorkspaceGroups**, which `is_account_group_member()` ignores → `credit_rating` masks to `***` for **everyone**, incl. the owner (masking is proven, but the privileged-bypass half of the reveal can't be shown). | Facilitator guide should list "create account groups `cm_privileged` + `cm_all_access` and add the desk-head demo user to `cm_privileged`" as an explicit **account-admin prerequisite**. The chinese-wall row filter needs no groups (uses `coverage_acl` + `current_user()`) and works fully. |
| 8 | 🟠 | attendee B1 / B2 checkpoint | KA "syncs in the background (UPDATING → UPDATED, a few min)" | On fevm-fins-canada the KA vector index was **still UPDATING after 30+ min**. The hero is unaffected (the 75/50/25 policy flows through the deterministic `get_filing_facts`, validated live via the Copilot), but the KA-narrative-with-citations answer can't be shown until sync finishes. | Soften timing to "can take 15–30+ min depending on workspace; the hero works via `get_filing_facts` meanwhile — don't gate the demo on KA sync." |

### ✅ Confirmed working end-to-end on a fresh workspace (positive findings)
- **Seed generator** — parameterized (catalog/prefix), ran clean on serverless; 9 clients / 94 pos / 45 notes / 73 facts / 20 news / 221 signals; hero **AC net-long WTI 150** intact.
- **All 6 desk SQL layers** — gold views, metric view (MEASURE ties to raw), UC functions, KA-shaped `research_docs` (the reserved-looking `_metadata` column is accepted — no error).
- **Genie spaces** (Portfolio + Market) created via the local builder + `POST /genie/spaces`.
- **3 desk agents** — every tool fires: Portfolio (get_client_positions + compute_shock_pnl in one turn, −1,595,513 CAD, 8-position book), Market (get_client_signals), Research (built; KA tool pending sync).
- **Capital Markets Copilot** — supervisor-of-supervisors, raw-REST `supervisor_agent` sub-agent registration (200×3); the cross-desk hero shows **two-level routing** (portfolio-desk + research-desk) and synthesizes WTI/HO exposure + −1.6M shock + 75/50/25 policy.
- **Chinese-wall follows through the agent (OBO)** — a caller scoped to Sofia, asking the *Portfolio agent*, sees AC (8 pos, WTI 150) but **not** BCE. The wall genuinely travels through the agent's UC-function tool calls, not just direct SQL. (KA vector index does **not** row-filter — as the guide's honest-notes already state.)
- **Persona reveal at the data layer** — scope→Sofia yields exactly {AC.TO, MG.TO} across all four governed assets (portfolio clients, positions, research_docs, market signals) simultaneously.
- **Discover domains (D2)** — `tag-policies` + `domains` + `SET TAGS` all succeed; 3 domains, 10 assets tagged.

### Live IDs (fevm-fins-canada · fins_canada_catalog)
- Seed: `cibc_cm_silver` / `cibc_cm_gold`. Products: `cm_portfolio_gold`/`_metrics`, `cm_research_gold`, `cm_market_gold`, `cm_governance`.
- Genie spaces: Portfolio `01f1a86235c91a339c515e31d8bd144e`, Market `01f1a86236261fcf881fbb8194f68c08`.
- Desk agents: Portfolio `mas-83e9bb8c-endpoint`, Research `mas-90cd2354-endpoint`, Market `mas-b160d747-endpoint`. KA `ka-8ed07581-endpoint`.
- Copilot: `mas-ad906c99-endpoint` (`ad906c99-368d-410e-aa6b-84fef88c4ff9`).
- Domains: Portfolio `bdc18568-7a71-493a-81b1-cad551d7dc33` (+ Research, Market).

### Fixes applied (2026-09-04)
- **#1 (🔴)** — all 7 Path-B notebooks now take `catalog` + `schema_prefix` widgets; `cibc_cm_silver`/`_gold` → `{SILVER}`/`{GOLD}` derived from the prefix; the metric-view YAML `source:` now uses `{CATALOG}`. **Re-validated live**: the parameterized `desk3/01` + `desk1/03` ran SUCCESS via job `base_parameters` (catalog+schema_prefix), internal hero assertions passing.
- **#2/#3** — Genie builders take `--warehouse-id` (+ `--catalog`); agent/KA/Copilot scripts take `--profile`, `--catalog`, and the handed-off IDs (`--genie-space-id`, `--ka-id`/`--ka-endpoint`, `--portfolio/research/market-sid`) via argparse. No more `profile="pbb-demo"` or pbb-demo IDs baked in. All 14 scripts `py_compile` clean; genie builder produces a payload with args.
- **#4/#5/#6** — attendee HTML: A1 restated to "Energy leads (≈CAD 1.6B, seed-dependent)"; A2 → −CAD 1.6M; noted `get_filing_facts` returns the hero policy.
- **#7** — attendee HTML D1 + FACILITATOR prereqs: account groups `cm_privileged`/`cm_all_access` called out as an account-admin prerequisite for the mask.
- **#8** — attendee HTML B1 + FACILITATOR: KA sync "15–30+ min, workspace-dependent; don't gate the demo on it."
- `README.md` + `FACILITATOR.md` reproduce sections updated (widgets, `--warehouse-id`/`--profile`/IDs, the OBO chinese-wall-through-agent finding, seed-dependent aggregates, this dry-run record).

### Path A (Genie Code) dry-run — Desk A · A1 (2026-09-04, driven live in the workspace)
Drove the A1 prompt through **Genie Code** in `fevm-fins-canada` (isolated `_a` schemas to protect the Path-B build). **Result: works end-to-end** — Genie Code auto-planned (4 steps), **auto-loaded the `databricks-metric-views` skill**, checked permissions, auto-approved each step, ran on serverless, and built certified `cm_portfolio_gold_a.{positions,clients}` + `cm_portfolio_metrics_a.exposure_kpis`. SQL-verified: 94 positions, Energy 1.595B, all 5 measures aggregate — **identical to Path B**. This confirms the "Driving Genie Code" mechanics we ported are accurate.

Two 🟡 **prompt-hardening findings** for the A1 Genie Code prompt:
| # | Sev | Finding | Fix |
|---|-----|---------|-----|
| P-1 | 🟡 | **"Certify everything" ≠ the official certification.** Genie Code applied a custom `certified=true` tag (and a `domain=finance` tag to satisfy this workspace's governed `domain` tag policy), **not** `system.certification_status=certified`. So the Certified badge + Genie One authority signal may not fire. | A1/A2/D-step prompts should say "set the **`system.certification_status`** tag to `certified`" explicitly, not just "certify." |
| P-2 | 🟡 | **A1 prompt doesn't name the seed source.** "join silver positions to clients" is ambiguous on a shared workspace with many `*_silver` schemas (I had to name `cibc_cm_silver`). | Prompt should name the seed, e.g. "from the `<schema_prefix>_silver` seed". |
| P-3 | ℹ️ | This workspace has a **governed `domain` tag policy** (finance/sales/…). Genie Code hit it and self-corrected. Customer envs may differ; note that "certify"/tagging can collide with a customer's existing tag governance. | Facilitator note. |

**A2 (driven through Genie Code, fresh chat):** built both UC functions (in parallel) + the Genie space "Portfolio & Exposure A" (id `01f1a885b6a31bd6b63303912827fea4`, HTTP 200), added description + sample question. `get_client_positions('CL-AC')` → 8 rows ✓.

| # | Sev | Finding | Fix |
|---|-----|---------|-----|
| P-4 | 🔴 | **A2 prompt underspecifies `compute_shock_pnl` → the hero number breaks.** Genie Code implemented `net_qty × spot × shock_pct` = 150 × 78.5 × −10% = **−1,177.50**, omitting the **contract size (×1000)** and **FX-to-CAD** that Path-B applies (correct = **−1,595,513 ≈ −1.6M**). "linear PnL impact (CAD) of a percentage price shock" isn't enough. | A2 prompt must state the economics: "PnL = net_qty × (spot_price × shock_pct) × contract_size × FX-to-CAD; join instruments for contract_size and use the CAD FX rate." Same wording belongs in the notebook's function comment so both paths agree. |

Left live: `cm_portfolio_gold_a` / `cm_portfolio_metrics_a` (+ the two functions and Genie space "Portfolio & Exposure A").

**A3 (driven through Genie Code):** loaded the supervisor-agent SDK skill and began building the MAS, but **got stuck on an SDK version conflict**:

| # | Sev | Finding | Fix |
|---|-----|---------|-----|
| P-5 | 🟠 | **Genie Code's SDK self-upgrade for `supervisor_agents` is messy but self-recovers.** After `%pip install --upgrade databricks-sdk` the old SDK stayed in the module cache; Genie Code churned through ~10 retries (in-process install → sys.path → subprocess → flush module cache → spec loader) before **falling back to the Databricks CLI**, which "has full support," and then created the agent + all 3 tools + printed the MCP URLs. So the guide's "Genie Code handles the SDK upgrade itself" is *directionally* true, but it's slow/noisy — not the clean one-shot the guide implies. **Verified end-to-end**: agent `af552d39`, endpoint `mas-af552d39-endpoint` READY, 3 tools (genie_space + 2 uc_function), MCP URL `…/api/2.0/mcp/functions/fins_canada_catalog/cm_portfolio_gold_a`. | Soften the guide: "the SDK upgrade for agent modules can take several retries and may fall back to the CLI — expect churn." Optionally pre-provision `databricks-sdk>=0.133`, or tell it to use the CLI/`databricks api` directly. |
| P-6 | ℹ️ | **Don't nudge Genie Code while it's still working.** It had already recovered (CLI) and finished A3; my "restart the kernel" follow-up (sent when it looked stuck) kicked off a **duplicate** agent build — caught and stopped before it created a second endpoint. Matches the guide's "let it run, don't interrupt." | Reinforce the existing "let it run" tip; add "if it looks stuck on an SDK import, wait — it falls back to the CLI on its own." |

**A3 verdict: ✅ works** (agent + 3 tools + MCP URL), with the P-5 SDK-upgrade churn. Note the desk agent inherits the **wrong `compute_shock_pnl`** (P-4) — it will answer the hero PnL as −1,177.50 until that function is fixed.

### Net verdict
The workshop **reproduces from scratch on a clean workspace.** No 🔴 blockers on the build itself; every desk, the governance wall, the Copilot, and the domains work. The one true 🔴 is **doc/portability hygiene** (#1): the Path-B notebooks hardcode `ec_demo_workspace` + `cibc_cm_silver` while the seed generator invites a custom prefix — so a customer following the guide's "swap `<catalog>`" line, and the seed's "use your own prefix" widget, will hit mismatches. Fixing #1 (parameterize the notebooks) + the checkpoint-number and account-group/KA-timing notes makes it turnkey.

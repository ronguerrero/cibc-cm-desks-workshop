# Facilitator guide — CM Data Products Workshop

## Shape
One firm, 3 desks. Each desk builds its own governed data product (Genie / KA / functions / metric
view / MCP) and a desk agent, then federates up to the firm-wide Copilot + Genie One. Two build
surfaces: **Genie Code prompts** (Path A, `PROMPT_RUNBOOK.md`) and **code notebooks** (Path B, per-desk
folders). Workspace `pbb-demo`, catalog `ec_demo_workspace`.

## Prerequisites — services & previews (facilitator, before the room)

### Services / features that must be available in the workspace
| Capability | Used for | Status / how to enable |
|---|---|---|
| **Unity Catalog** + a catalog you can create schemas in | everything | Required. Placeholder `<catalog>`. |
| **Serverless SQL warehouse** + serverless notebooks/jobs | seed, gold, functions, Genie spaces, governance | Required. Note the warehouse id — the Genie-space builders take `--warehouse-id`. |
| **Foundation Model APIs** — `databricks-claude-haiku-4-5` (or set `llm`) | seed `ai_query` (research/filings/news) | Must be **served in your region**; docs lag, so check `system.ai` / serving endpoints directly. |
| **AI features / `ai_query`** enabled | seed text tables; Genie | Admin Console → **Feature enablement → AI/BI**. If off, `ai_query` fails and Genie returns `FAILED / NO_DEPLOYMENTS`. |
| **Metric views** | Desk 1 semantic layer | GA. |
| **ABAC** column masks + row filters (`SET MASK` / `SET ROW FILTER`) | governance wall | GA. Mask needs **account groups** (below). |
| **Change Data Feed** | KA source table | GA (the notebook sets it). |
| **Agent Bricks — Knowledge Assistant** | Desk 2 KA | Must be enabled/available in your region. Path B needs **databricks-sdk ≥ 0.133**. |
| **Agent Bricks — Multi-Agent Supervisor** (Supervisor Agent) | every desk agent + the Copilot | Must be enabled/available. Path B needs **databricks-sdk ≥ 0.133**. |
| **Genie** (spaces) | Desk 1 & 3 spaces | GA. |
| **Genie One + chat/routing** | front door A (discovery) | Genie One GA; **chat/routing is Public Preview — enroll it**. Ranking is stochastic (~98% consistent). |
| **Genie + KA composition in Genie One** | (avoid) | **Private Preview**, single-space, UI-only, fragile — don't rely on it; the **Copilot** is the GA path for structured+unstructured composition. |
| **Discover domains** | D2 data-product boundaries | **Public Preview — enroll**. Discover **Pages** are Beta (hand-authored, no public API). |
| **Managed MCP** (`/api/2.0/mcp/...`) | expose UC funcs/Genie/KA as MCP | GA. |
| **External MCP → UC** (HTTP Connection + MCP Service) | attach a 3rd-party MCP (recipe R1) | **Public Preview** (REST/SDK, no SQL DDL). |
| **Custom MCP as a Databricks App** | R1 alternative | GA. |

### Identity / permissions
- **Account admin** to create account groups **`cm_privileged`** (rating-mask bypass) and
  **`cm_all_access`** (chinese-wall bypass); add the desk-head demo user to `cm_privileged`. The mask
  keys off `is_account_group_member('cm_privileged')`, which only recognizes **account** groups — a
  workspace-local group won't work, and without it `credit_rating` masks to `***` for everyone. (The
  chinese-wall row filter itself needs no groups — it uses `coverage_acl` + `current_user()`.)
- Workspace permissions to create schemas, serving endpoints, Genie spaces, and Discover domains.

### Seed + parameters
- Run `data/01_generate_seed.py` with your `catalog` + a fresh `schema_prefix` (fresh workspace), or
  `data/00_verify_foundation.py` to confirm an existing seed. **The same `catalog` + `schema_prefix`
  widgets carry into every Path-B desk notebook** — keep them identical. Genie-space builders take
  `--warehouse-id`; the agent/KA/Copilot scripts take `--profile` + the IDs earlier steps hand off.
  Desk *product* schemas (`cm_portfolio_gold`, etc.) are fixed names.

## Suggested agenda (half-day core, ~4h)
1. **Kickoff + data foundation (20m)** — run `data/01_generate_seed.py` (fresh) or
   `data/00_verify_foundation.py` (existing seed); the shared CM world.
2. **Parallel desk build (~2.5h)** — three groups, one desk each:
   - Desk 1 Portfolio (code-led): gold → metric view → functions → Genie → desk agent.
   - Desk 2 Research (Genie-Code-led): research corpus → KA → filing facts → desk agent.
   - Desk 3 Market Intel (mixed): news gold → Genie → signal function → desk agent.
   Each desk ends with a live desk MAS answering its hero question.
3. **Govern → data product (40m)** — `governance/01_abac_and_rls.py`: certify, mask, chinese-wall.
4. **Federate (40m)** — `federation/`: register desks into the Copilot; domains; Genie One discovery.
5. **Persona reveal + traces (30m)** — the two-login demo; MLflow trace of a cross-desk route.

## The persona reveal (money shot)
Same question, two identities, different governed answers.
1. As full-access (desk head): ask the Copilot *"For Air Canada: oil exposure, PnL if WTI drops 10%,
   and the house view on fuel hedging."* → composes Portfolio + Research desks.
2. Scope a user to one coverage officer (chinese-wall):
   ```sql
   -- as-if 'Sofia Martins' (covers AC, MG)
   DELETE FROM ec_demo_workspace.cm_governance.coverage_acl WHERE user_email='<demo_user>';
   INSERT INTO ec_demo_workspace.cm_governance.coverage_acl VALUES ('<demo_user>','Sofia Martins');
   ```
   Now that user sees only AC.TO + MG.TO across clients, positions, research, and signals — same
   query, restricted result. Restore by re-inserting the other officers.
3. Show `credit_rating` masked (`***`) unless the caller is in the `cm_privileged` account group.

## Reset / cleanup
- Restore full access: re-insert all three officers into `coverage_acl` for the owner.
- **Stop idle cost:** MAS/KA endpoints scale to zero; no manual stop needed. (No Lakebase in this build.)
- Rebuild any desk from its notebooks (idempotent `CREATE OR REPLACE`).

## Honest talking points (verified)
- Genie One = broad rank-based discovery (OntoRank), **no registration API**, chat/routing is Public
  Preview, ranking stochastic (~98%). Genie + KA composition in Genie One is **Private Preview**.
- **Use the Copilot (Supervisor Agent, GA) for reliable structured+unstructured composition.**
- KA vector index doesn't enforce per-caller row filters — chinese-wall holds on structured paths.
  The chinese-wall **does** follow through the desk agents (OBO) on the structured/function paths —
  verified: a caller scoped to one officer sees their client via the agent but not others'.
- **KA sync takes time** — allow **15–30+ min** (workspace-dependent), not "a few minutes". Don't
  gate the demo on it: the hero fuel-hedge policy flows through the deterministic `get_filing_facts`.
- External MCP → UC is Public Preview; managed MCP + custom-App MCP are GA.
- Aggregate numbers are **seed-dependent** (e.g. Energy gross notional ≈ CAD 1.6B on the generator
  seed). The hard-seeded hero (AC WTI/HO, −CAD 1.6M shock, 75/50/25 policy) reproduces exactly.

## Reproduce on a customer workspace
Everything is generated or public. Reuse the Bellwether generators for the seed; swap `<catalog>`.
The `recipes/` cards (R1–R5) are the lift-and-shift entry points for a customer's own data.

# Desk 1 — Portfolio & Exposure

The structured / quant desk. Builds a governed data product over client positions and exposures,
then composes it into a shareable desk agent. **Lead surface: code notebooks (Path B).**

Run order (each notebook has a validation cell):

| Step | File | Builds | Live IDs (pbb-demo) |
|---|---|---|---|
| D1.1 | `01_gold_views.py` | `cm_portfolio_gold.positions`, `.clients` (certified) | — |
| D1.2 | `02_metric_view.py` | `cm_portfolio_metrics.exposure_kpis` (certified) | — |
| D1.3 | `03_uc_functions.py` | `get_client_positions`, `compute_shock_pnl` | — |
| D1.4 | `04_genie_space.py` | Genie space "Portfolio & Exposure — CM Desk" | `01f1a7d4c80a1e6c935c8f5fdc77e543` |
| D1.5 | `05_mcp.md` | managed MCP (URLs) + public/ external MCP notes | — |
| D1.6 | `06_desk_agent.py` | **Portfolio Desk Agent** (MAS, 3 tools) | `mas-5e43b418-endpoint` |

**Validated live (2026-09-03):** "WTI −10% for Air Canada + show its book" → the desk agent routed
`compute_shock_pnl` (−CAD 1,575,153) **and** `get_client_positions` (8 positions) in one turn.

Requirements: notebooks D1.1–D1.4 run on any pbb-demo compute (SQL/Spark). D1.6 needs
`databricks-sdk>=0.133` (`w.supervisor_agents`). Catalog `ec_demo_workspace`, warehouse
`cf771eb9a270a746`.

Genie Code (Path A) equivalents for every step are in the root `PROMPT_RUNBOOK.md`.

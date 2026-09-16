# Desk 3 — Market Intelligence

The external-signals desk. Tagged market news + client signal matches, exposed via a Genie space
and a signal function. **Lead surface: mixed** (structured Genie + function; public news MCP).

| Step | File | Builds | Live IDs (pbb-demo) |
|---|---|---|---|
| D3.1+D3.3 | `01_gold_and_function.py` | `cm_market_gold.news_events`, `.signal_matches` (certified) + `get_client_signals` | — |
| D3.2 | `04_genie_space.py` | Market Intelligence Genie space | `01f1a7d7670719e5b46a73d654d41bca` |
| D3.5 | `05_mcp.md` | managed MCP + public Scout/GDELT MCP notes | — |
| D3.6 | `06_desk_agent.py` | **Market Intel Desk Agent** (MAS: Genie + get_client_signals) | `mas-cb2e43fd-endpoint` |

**Validated live (2026-09-03):** the desk agent routed to Genie for "which clients are exposed to
oil (WTI) news" → returned exposed clients with a bearish-dominant sentiment breakdown (OPEC+
supply hikes, Goldman cut). `get_client_signals('CL-AC')` returns AC's WTI/USDCAD news signals.

**Design note:** Desk 3 leads with a **Genie + function** combo (structured, no vector-index sync)
to contrast Desk 2's managed-KA path. The DIY Vector-Search route for "vectorize my own docs" is
documented as recipe **R2** (route B) rather than duplicated here.

Requirements: D3.1 runs on any pbb-demo compute; D3.6 needs `databricks-sdk>=0.133`.

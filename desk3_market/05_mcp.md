# Desk 3 · D3.5 — MCP server

## (a) Managed MCP (GA) — expose our own
- Signal function: `/api/2.0/mcp/functions/ec_demo_workspace/cm_market_gold`
- Market Intel Genie: `/api/2.0/mcp/genie/01f1a7d7670719e5b46a73d654d41bca`

## (b) Public news/market MCP (zero-key)
- **`market-research-mcp`** ("Scout", pedrobraiti, MIT, **no API keys**) — 62 tools bundling GDELT
  news/events, FRED, yfinance, sentiment. Strongest reproducibility (no keys, no copyleft).
- No dedicated public GDELT-only MCP exists (Scout wraps it); our own pbb-demo GDELT MCP is the alt.

## (c) Attach the customer's existing external MCP → recipe R1
Register as UC HTTP Connection + MCP Service (Public Preview). See `recipes/` R1.

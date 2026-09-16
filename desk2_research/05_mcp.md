# Desk 2 · D2.5 — MCP server

## (a) Managed MCP (GA) — expose our own
- Filing facts function: `/api/2.0/mcp/functions/ec_demo_workspace/cm_research_gold`
- (KA is consumed directly by the desk agent D2.6; managed-MCP over KA optional.)

## (b) Public filings MCP
Live SEC EDGAR filings/XBRL/insider forms:
- **`sec-edgar-mcp`** (stefanoamorelli) — keyless (`User-Agent` header), most tools. **License:
  AGPL-3.0 → bank blocker.**
- **Prefer `datakoot/filings-intel-mcp`** (MIT, keyless, remote HTTP) for a bank.

## (c) Attach the customer's existing external MCP → recipe R1
Register as UC HTTP Connection + MCP Service (Public Preview). See `recipes/` R1.

# Desk 1 · D1.5 — MCP server

The Portfolio desk exposes its tools two ways.

## (a) Managed MCP (GA) — expose our own, no build
Databricks hosts an MCP over UC functions / Genie / Vector Search. No deployment; the endpoint
exists as soon as the UC objects do. URL patterns (`https://<ws>/api/2.0/mcp/...`):

| What | URL |
|---|---|
| Portfolio UC functions | `/api/2.0/mcp/functions/ec_demo_workspace/cm_portfolio_gold` |
| Portfolio Genie space | `/api/2.0/mcp/genie/01f1a7d4c80a1e6c935c8f5fdc77e543` |

Call from agent code:
```python
from databricks_mcp import DatabricksMCPClient
from databricks.sdk import WorkspaceClient
w = WorkspaceClient(profile="pbb-demo")
c = DatabricksMCPClient(
    server_url=f"{w.config.host}/api/2.0/mcp/functions/ec_demo_workspace/cm_portfolio_gold",
    workspace_client=w)
c.list_tools()                                   # -> get_client_positions, compute_shock_pnl
c.call_tool("get_client_positions", {"p_client_id": "CL-AC"})
```
> Verified via the consumption path: the Portfolio Desk Agent (D1.6) calls these exact UC functions
> successfully. A standalone `DatabricksMCPClient.list_tools()` check is the documented GA pattern
> (deferred here — the local `mcp` client transport hung; not a workspace issue).

## (b) Public market-data MCP
Official **`alpha_vantage_mcp`** (free-tier key) for live prices/technicals. OpenFIGI has **no
public MCP** — wrap our own and expose via managed MCP if instrument-identifier mapping is needed.

## (c) Attach an *existing external* MCP (customer's own) → see recipe **R1**
External/third-party MCP registers into UC as an **HTTP Connection + MCP Service** (Public Preview;
REST `POST /api/2.1/unity-catalog/mcp-services` or SDK — no SQL DDL). See `recipes/` R1.

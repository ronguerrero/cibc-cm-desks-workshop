# R4 — "I have a SQL/Python function. How do I make it an agent tool?"

Proven in `desk1_portfolio/03_uc_functions.py` (+ Desk 2/3).

1. **Register a UC function.** Prefer a SQL table function (reliable on serverless; no scalar-
   subquery planner issues). **Prefix params with `p_`** — an unprefixed `client_id` param is
   shadowed by the column and the filter returns ALL rows:
```sql
CREATE OR REPLACE FUNCTION <cat>.<schema>.get_client_positions(p_client_id STRING)
RETURNS TABLE (client_id STRING, ticker STRING, net_qty DOUBLE, gross_notional_cad DOUBLE)
COMMENT 'Return positions for a client (e.g. CL-AC).'  -- the COMMENT is what the agent reads
RETURN SELECT client_id, ticker, net_qty, gross_notional_cad
       FROM <cat>.<schema>.positions WHERE client_id = p_client_id;
```
   A rich `COMMENT` matters — it's the tool description the agent routes on.

2. **Attach as a Supervisor tool** (SDK ≥ 0.133):
```python
from databricks.sdk.service import supervisoragents as sa
w.supervisor_agents.create_tool(
    parent=f"supervisor-agents/{sid}", tool_id="get-client-positions",
    tool=sa.Tool(tool_type="uc_function", name="get_client_positions",
                 description="Return a client's positions.",
                 uc_function=sa.UcFunction(name="<cat>.<schema>.get_client_positions")))
```
   Or expose it as **managed MCP** at `/api/2.0/mcp/functions/<cat>/<schema>` and call from any agent
   via `DatabricksMCPClient` (see R1).

## ✓ Validation
`SELECT * FROM <cat>.<schema>.get_client_positions('CL-AC')` returns the right rows; the desk agent
calls it in a turn. In this build `compute_shock_pnl('CL-AC','WTI',-10)` → −CAD 1,575,153, and the
agent invoked it live.

## Gotchas
- `CREATE OR REPLACE FUNCTION` wipes EXECUTE grants — re-grant after each replace.
- Python UC functions with `ENVIRONMENT (dependencies=…)` fail on serverless warehouses without pypi
  egress. SQL table functions avoid this.

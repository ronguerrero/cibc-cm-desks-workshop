# R1 — "I already run an MCP server. How do I attach it to UC and my agent?"

Three shapes of MCP on Databricks — branch on which you have. (Verified 2026-09-03; confirm exact
SDK signatures against your installed SDK.)

## (a) External / third-party MCP you already run → register in Unity Catalog
**UC HTTP Connection + "MCP Service" wrapper.** Public Preview. **No SQL DDL** — use REST or SDK.

1. Create a UC connection to your MCP server (bearer token via secret, OAuth M2M/U2M, or DCR):
```sql
CREATE CONNECTION my_mcp_conn TYPE HTTP
OPTIONS (host 'https://my-mcp.example.com', port '443', base_path '/',
         bearer_token secret('my_scope','my_mcp_token'));
```
2. Register it as an MCP Service (governed in UC) — REST:
```bash
databricks api post /api/2.1/unity-catalog/mcp-services --profile <p> --json '{
  "parent": "schemas/<catalog>.<schema>",
  "mcp_service_id": "my_mcp",
  "config": {"source_connection": {"name": "connections/<catalog>.<schema>.my_mcp_conn"}}
}'
```
(SDK equivalent: `w.ai_gateway.create_mcp_service(...)` — verify the method name in your SDK build.)

## (b) Expose your OWN UC functions / Genie / Vector Search as MCP (managed, GA)
No build — the endpoint exists once the UC objects do:
```
https://<ws>/api/2.0/mcp/functions/<catalog>/<schema>        # all functions in a schema
https://<ws>/api/2.0/mcp/genie/<space_id>
https://<ws>/api/2.0/mcp/ai-search/<catalog>/<schema>/<index>
https://<ws>/api/2.0/mcp/sql
```

## (c) Your own MCP server hosted as a Databricks App (GA) — endpoint `/mcp`.

## Attach to an agent
- **Supervisor Agent:** register a tool pointing at the MCP Service URL
  `https://<ws>/ai-gateway/mcp-services/<catalog>.<schema>.<id>`.
- **Custom Mosaic AI agent (code):**
```python
from databricks_mcp import DatabricksMCPClient
from databricks.sdk import WorkspaceClient
w = WorkspaceClient(profile="pbb-demo")
c = DatabricksMCPClient(
    server_url=f"{w.config.host}/api/2.0/mcp/functions/ec_demo_workspace/cm_portfolio_gold",
    workspace_client=w)
c.list_tools()                                     # discover
c.call_tool("get_client_positions", {"p_client_id": "CL-AC"})
```

## ✓ Validation
`list_tools()` returns your server's tools; the agent can `call_tool(...)`. In this build the
Portfolio Desk Agent calls the managed-MCP UC functions successfully (proven consumption path).

# From-scratch recipe cards

Lift-one-without-the-whole-workshop recipes, keyed to what a customer actually asks. Each distills
a pattern **proven live** in this build (see `BUILD_LOG.md`). Every card carries the code (Path B)
and the Genie Code prompt (Path A) plus a validation check.

| # | "I want to…" | Pattern | Proven in |
|---|---|---|---|
| [R1](R1_attach_existing_mcp.md) | attach my existing MCP server to UC + my agent | UC HTTP Connection + MCP Service; `databricks-mcp` client | Desk MCP (D*.5) |
| [R2](R2_vectorize_my_docs.md) | vectorize my documents and query them | KA `file_table` (no Volume) or raw Vector Search | Desk 2 KA |
| [R3](R3_tables_to_genie_agent.md) | make a Genie agent over my tables | gold view → metric view → certify → Genie space | Desk 1 / Desk 3 |
| [R4](R4_function_to_tool.md) | turn my SQL/Python function into an agent tool | UC function (`p_`-prefixed) → MAS `uc_function` tool | Desk 1/2/3 |
| [R5](R5_share_to_org.md) | share my product to the org | certify + domain + register into Copilot / Genie One | Phase 4 |

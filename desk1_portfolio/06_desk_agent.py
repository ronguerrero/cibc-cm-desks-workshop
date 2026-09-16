#!/usr/bin/env python3
"""
Desk 1 · D1.6 — Portfolio Desk Agent (Multi-Agent Supervisor).

Composes the desk's tools into one shareable desk-level agent (hybrid topology, PLAN.md):
  - Genie space  (D1.4)  -> exposure/notional/PnL aggregates + position lookups
  - get_client_positions (D1.3) -> a named client's book
  - compute_shock_pnl    (D1.3) -> price-shock PnL impact

Requires databricks-sdk >= 0.133 (w.supervisor_agents). Run with such a venv, profile pbb-demo.
Genie Code prompt equivalent: RUNBOOK D1.6 (databricks-agent-bricks skill).
"""
from databricks.sdk import WorkspaceClient
from databricks.sdk.service import supervisoragents as sa

import argparse
_p = argparse.ArgumentParser()
_p.add_argument("--profile", default="pbb-demo")
_p.add_argument("--catalog", default="ec_demo_workspace")
_p.add_argument("--genie-space-id", required=True, help="Portfolio Genie space id from D1.4")
_a = _p.parse_args()
CATALOG = _a.catalog
GENIE_SPACE_ID = _a.genie_space_id

w = WorkspaceClient(profile=_a.profile)

agent = w.supervisor_agents.create_supervisor_agent(
    sa.SupervisorAgent(
        display_name="Portfolio Desk Agent",
        description="Portfolio & Exposure desk agent: client positions, exposures, and price-shock PnL.",
        instructions=(
            "You are the Portfolio & Exposure desk agent for a capital-markets trading floor. "
            "Route: use the Genie space for exposure / gross notional / net exposure / unrealized PnL "
            "roll-ups (by sector, desk, currency, asset class) and for which clients hold an instrument; "
            "use get_client_positions for a single named client's book; use compute_shock_pnl for the "
            "PnL impact of a percentage price shock on a client's instrument (e.g. WTI down 10%). "
            "Amounts are CAD. Be concise and state assumptions."
        ),
    )
)
sid = agent.supervisor_agent_id
parent = f"supervisor-agents/{sid}"
print("created supervisor:", sid, "endpoint:", agent.endpoint_name)

w.supervisor_agents.create_tool(
    parent=parent, tool_id="portfolio-genie",
    tool=sa.Tool(tool_type="genie_space", name="portfolio_exposure_genie",
                 description="Structured exposure/notional/PnL analytics for the Portfolio desk.",
                 genie_space=sa.GenieSpace(id=GENIE_SPACE_ID)),
)
w.supervisor_agents.create_tool(
    parent=parent, tool_id="get-client-positions",
    tool=sa.Tool(tool_type="uc_function", name="get_client_positions",
                 description="Return all positions for a given client_id (e.g. CL-AC).",
                 uc_function=sa.UcFunction(name=f"{CATALOG}.cm_portfolio_gold.get_client_positions")),
)
w.supervisor_agents.create_tool(
    parent=parent, tool_id="compute-shock-pnl",
    tool=sa.Tool(tool_type="uc_function", name="compute_shock_pnl",
                 description="Linear PnL impact (CAD) of a percentage price shock on a client position.",
                 uc_function=sa.UcFunction(name=f"{CATALOG}.cm_portfolio_gold.compute_shock_pnl")),
)

tools = list(w.supervisor_agents.list_tools(parent=parent))
print("tools:", [(t.tool_type, t.name) for t in tools])
print("ENDPOINT_NAME", agent.endpoint_name)

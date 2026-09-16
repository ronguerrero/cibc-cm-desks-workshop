#!/usr/bin/env python3
"""Desk 3 · D3.6 — Market Intel Desk Agent (MAS). Tools: Market Intel Genie + get_client_signals.
Hybrid topology: 2+ tools => own desk MAS. Requires databricks-sdk >= 0.133."""
from databricks.sdk import WorkspaceClient
from databricks.sdk.service import supervisoragents as sa

import argparse
_p = argparse.ArgumentParser()
_p.add_argument("--profile", default="pbb-demo")
_p.add_argument("--catalog", default="ec_demo_workspace")
_p.add_argument("--genie-space-id", required=True, help="Market Intel Genie space id from D3.2")
_a = _p.parse_args()
CATALOG = _a.catalog
GENIE_SPACE_ID = _a.genie_space_id
w = WorkspaceClient(profile=_a.profile)

agent = w.supervisor_agents.create_supervisor_agent(
    sa.SupervisorAgent(
        display_name="Market Intel Desk Agent",
        description="Market Intelligence desk agent: news sentiment / adverse media and client signal exposure.",
        instructions=(
            "You are the Market Intelligence desk agent. Use the Genie space for news, sentiment / "
            "adverse-media questions and to find which clients are exposed to a market event. Use "
            "get_client_signals for a single named client's news-signal exposure. Client ids look "
            "like CL-AC (Air Canada). Be concise."
        ),
    )
)
sid = agent.supervisor_agent_id
parent = f"supervisor-agents/{sid}"
print("created supervisor:", sid, "endpoint:", agent.endpoint_name)

w.supervisor_agents.create_tool(
    parent=parent, tool_id="market-genie",
    tool=sa.Tool(tool_type="genie_space", name="market_intel_genie",
                 description="News sentiment, adverse media, and client signal exposure analytics.",
                 genie_space=sa.GenieSpace(id=GENIE_SPACE_ID)),
)
w.supervisor_agents.create_tool(
    parent=parent, tool_id="get-client-signals",
    tool=sa.Tool(tool_type="uc_function", name="get_client_signals",
                 description="News events a client is exposed to, with sentiment and position/PnL.",
                 uc_function=sa.UcFunction(name=f"{CATALOG}.cm_market_gold.get_client_signals")),
)
print("ENDPOINT_NAME", agent.endpoint_name)

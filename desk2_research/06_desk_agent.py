#!/usr/bin/env python3
"""
Desk 2 · D2.6 — Research Desk Agent (Multi-Agent Supervisor).

Tools: Research KA (D2.3, unstructured house-view retrieval) + get_filing_facts (D2.2, structured
filing facts). Hybrid topology: 2+ tools => own desk MAS. Requires databricks-sdk >= 0.133.
"""
from databricks.sdk import WorkspaceClient
from databricks.sdk.service import supervisoragents as sa

import argparse
_p = argparse.ArgumentParser()
_p.add_argument("--profile", default="pbb-demo")
_p.add_argument("--catalog", default="ec_demo_workspace")
_p.add_argument("--ka-id", required=True, help="Research KA id from D2.3")
_p.add_argument("--ka-endpoint", required=True, help="Research KA serving endpoint (ka-…-endpoint) from D2.3")
_a = _p.parse_args()
CATALOG = _a.catalog
KA_ID = _a.ka_id
KA_ENDPOINT = _a.ka_endpoint

w = WorkspaceClient(profile=_a.profile)

agent = w.supervisor_agents.create_supervisor_agent(
    sa.SupervisorAgent(
        display_name="Research Desk Agent",
        description="Research & Filings desk agent: analyst house views + structured filing facts.",
        instructions=(
            "You are the Research & Filings desk agent. Use the Research KA for qualitative house "
            "views, hedging strategy narrative, and risk commentary; use get_filing_facts for exact "
            "structured facts from a client's filings (hedge_policy, hedge_ratio, derivative_notional, "
            "commodity/fx/rate_exposure, covenant). Prefer get_filing_facts when the user asks for a "
            "specific number or policy. Cite sources. Client ids look like CL-AC (Air Canada)."
        ),
    )
)
sid = agent.supervisor_agent_id
parent = f"supervisor-agents/{sid}"
print("created supervisor:", sid, "endpoint:", agent.endpoint_name)

w.supervisor_agents.create_tool(
    parent=parent, tool_id="research-ka",
    tool=sa.Tool(tool_type="knowledge_assistant", name="research_filings_ka",
                 description="Analyst research house-views, hedging strategy, and risk commentary.",
                 knowledge_assistant=sa.KnowledgeAssistant(
                     knowledge_assistant_id=KA_ID, serving_endpoint_name=KA_ENDPOINT)),
)
w.supervisor_agents.create_tool(
    parent=parent, tool_id="get-filing-facts",
    tool=sa.Tool(tool_type="uc_function", name="get_filing_facts",
                 description="Structured facts from a client's filings (hedge policy, ratios, notionals, covenants).",
                 uc_function=sa.UcFunction(name=f"{CATALOG}.cm_research_gold.get_filing_facts")),
)

tools = list(w.supervisor_agents.list_tools(parent=parent))
print("tools:", [t.tool_type for t in tools])
print("ENDPOINT_NAME", agent.endpoint_name)

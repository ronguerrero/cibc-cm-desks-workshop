#!/usr/bin/env python3
"""
Phase 4 · S3-B — Capital Markets Copilot (supervisor-of-supervisors).

Registers each desk MAS as a `supervisor_agent` sub-agent tool. NOTE: as of databricks-sdk 0.134
the `Tool` dataclass has no `supervisor_agent` spec field (the API supports the tool_type but the
SDK lags), so sub-agent tools are created via raw REST POST /api/2.1/supervisor-agents/{id}/tools
with body {"tool_type":"supervisor_agent","supervisor_agent":{"supervisor_agent_id":"<id>"}}.
"""
import requests
from databricks.sdk import WorkspaceClient
from databricks.sdk.service import supervisoragents as sa

import argparse
_p = argparse.ArgumentParser()
_p.add_argument("--profile", default="pbb-demo")
_p.add_argument("--portfolio-sid", required=True, help="Portfolio Desk Agent supervisor_agent_id (D1.6)")
_p.add_argument("--research-sid", required=True, help="Research Desk Agent supervisor_agent_id (D2.6)")
_p.add_argument("--market-sid", required=True, help="Market Intel Desk Agent supervisor_agent_id (D3.6)")
_a = _p.parse_args()
w = WorkspaceClient(profile=_a.profile)

DESKS = [  # (tool_id, name, description, desk supervisor_agent_id)
    ("portfolio-desk", "portfolio_desk_agent",
     "Portfolio & Exposure desk: client positions, exposures, price-shock PnL.",
     _a.portfolio_sid),
    ("research-desk", "research_desk_agent",
     "Research & Filings desk: analyst house views and filing facts (hedging policy, covenants).",
     _a.research_sid),
    ("market-desk", "market_intel_desk_agent",
     "Market Intelligence desk: news sentiment, adverse media, client news-signal exposure.",
     _a.market_sid),
]

copilot = w.supervisor_agents.create_supervisor_agent(sa.SupervisorAgent(
    display_name="Capital Markets Copilot",
    description="Firm-wide CM copilot routing across desk agents (Portfolio, Research, Market Intelligence).",
    instructions=(
        "You are the firm-wide Capital Markets Copilot. Route each question to the right desk agent: "
        "Portfolio for positions/exposure/PnL and price-shock impact; Research for analyst house views "
        "and filing facts; Market Intel for news/sentiment/adverse-media and client news-signal exposure. "
        "For a question spanning desks (e.g. a client's oil exposure AND the house view), call multiple "
        "desk agents and synthesize. Amounts CAD. Answers are already governed (masks/row filters)."),
))
cid = copilot.supervisor_agent_id
print("COPILOT", cid, copilot.endpoint_name)

# Register each desk MAS as a supervisor_agent sub-agent tool via raw REST
base = w.config.host
headers = {**w.config.authenticate(), "Content-Type": "application/json"}
for tool_id, name, desc, desk_sid in DESKS:
    url = f"{base}/api/2.1/supervisor-agents/{cid}/tools?tool_id={tool_id}"
    body = {"tool_type": "supervisor_agent", "name": name, "description": desc,
            "supervisor_agent": {"supervisor_agent_id": desk_sid}}
    r = requests.post(url, headers=headers, json=body, timeout=60)
    print("  +", tool_id, r.status_code)

print("COPILOT_ENDPOINT", copilot.endpoint_name)

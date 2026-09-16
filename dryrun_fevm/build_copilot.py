#!/usr/bin/env python3
"""Phase 4 · Capital Markets Copilot (supervisor-of-supervisors) on fevm-fins-canada."""
import json, requests
from databricks.sdk import WorkspaceClient
from databricks.sdk.service import supervisoragents as sa

w = WorkspaceClient(profile="fevm-fins-canada")
h = json.load(open("/Users/elmer.cecilio/Claude_Projects/cibc-cm-desks-workshop/dryrun_fevm/handoff_ids.json"))
DESKS = [
    ("portfolio-desk","portfolio_desk_agent","Portfolio & Exposure desk: positions, exposures, price-shock PnL.", h["portfolio"]["sid"]),
    ("research-desk","research_desk_agent","Research & Filings desk: analyst house views and filing facts.", h["research"]["sid"]),
    ("market-desk","market_intel_desk_agent","Market Intelligence desk: news sentiment, adverse media, client news-signal exposure.", h["market"]["sid"]),
]
copilot = w.supervisor_agents.create_supervisor_agent(sa.SupervisorAgent(
    display_name="Capital Markets Copilot",
    description="Firm-wide CM copilot routing across desk agents (Portfolio, Research, Market Intelligence).",
    instructions=("You are the firm-wide Capital Markets Copilot. Route each question to the right desk agent: "
      "Portfolio for positions/exposure/PnL and price-shock impact; Research for analyst house views and filing "
      "facts; Market Intel for news/sentiment/adverse-media and client news-signal exposure. For a question spanning "
      "desks (e.g. a client's oil exposure AND the house view), call multiple desk agents and synthesize. Amounts CAD. "
      "Answers are already governed (masks/row filters)."),
))
cid = copilot.supervisor_agent_id
print("COPILOT", cid, copilot.endpoint_name)
base = w.config.host
headers = {**w.config.authenticate(), "Content-Type": "application/json"}
for tool_id, name, desc, desk_sid in DESKS:
    url = f"{base}/api/2.1/supervisor-agents/{cid}/tools?tool_id={tool_id}"
    body = {"tool_type":"supervisor_agent","name":name,"description":desc,"supervisor_agent":{"supervisor_agent_id":desk_sid}}
    r = requests.post(url, headers=headers, json=body, timeout=60)
    print("  +", tool_id, r.status_code, ("" if r.ok else r.text[:200]))
h["copilot"] = {"sid": cid, "endpoint": copilot.endpoint_name}
json.dump(h, open("/Users/elmer.cecilio/Claude_Projects/cibc-cm-desks-workshop/dryrun_fevm/handoff_ids.json","w"), indent=2)
# verify tools registered
tools = list(w.supervisor_agents.list_tools(parent=f"supervisor-agents/{cid}"))
print("copilot tools:", [(t.tool_type, t.name) for t in tools])
print("COPILOT_ENDPOINT", copilot.endpoint_name)

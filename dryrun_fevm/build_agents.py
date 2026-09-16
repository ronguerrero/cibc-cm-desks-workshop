#!/usr/bin/env python3
"""Dry-run: build KA (Desk B) + 3 desk agents on fevm-fins-canada. Captures hand-off IDs."""
import json
from databricks.sdk import WorkspaceClient
from databricks.sdk.service import supervisoragents as sa
from databricks.sdk.service import knowledgeassistants as ka

PROFILE = "fevm-fins-canada"
CATALOG = "fins_canada_catalog"
PORTFOLIO_SPACE = "01f1a86235c91a339c515e31d8bd144e"
MARKET_SPACE    = "01f1a86236261fcf881fbb8194f68c08"
w = WorkspaceClient(profile=PROFILE)
handoff = {}

# ---------- Desk B · B1: Knowledge Assistant ----------
print("=== Creating Research KA ===")
assistant = w.knowledge_assistants.create_knowledge_assistant(ka.KnowledgeAssistant(
    display_name="Research & Filings KA",
    description="Analyst research house-views and risk commentary for capital-markets clients.",
    instructions=("Answer questions about the desk's house view, hedging strategy, risks, and outlook "
                  "for capital-markets clients (e.g. Air Canada fuel hedging). Ground every answer in "
                  "the research corpus and cite the source note. If the corpus does not cover it, say so."),
))
print("KA:", assistant.id, assistant.name, assistant.endpoint_name)
src = w.knowledge_assistants.create_knowledge_source(
    parent=assistant.name,
    knowledge_source=ka.KnowledgeSource(
        display_name="Analyst research corpus",
        description="Initiations, quarterly updates, flash notes, risk notes, sector pieces per client.",
        source_type="file_table",
        file_table=ka.FileTableSpec(table_name=f"{CATALOG}.cm_research_gold.research_docs", file_col="content"),
    ),
)
print("KA source:", src.id, src.state)
try:
    w.knowledge_assistants.sync_knowledge_sources(name=assistant.name); print("sync requested")
except Exception as e:
    print("sync note:", e)
handoff["ka_id"] = assistant.id
handoff["ka_endpoint"] = assistant.endpoint_name

def mk(display, desc, instr):
    a = w.supervisor_agents.create_supervisor_agent(sa.SupervisorAgent(
        display_name=display, description=desc, instructions=instr))
    print("MAS:", display, a.supervisor_agent_id, a.endpoint_name)
    return a

def tool(sid, tool_id, t):
    w.supervisor_agents.create_tool(parent=f"supervisor-agents/{sid}", tool_id=tool_id, tool=t)

# ---------- Desk A · A3: Portfolio Desk Agent ----------
print("=== Portfolio Desk Agent ===")
pa = mk("Portfolio Desk Agent",
        "Portfolio & Exposure desk agent: client positions, exposures, and price-shock PnL.",
        ("You are the Portfolio & Exposure desk agent for a capital-markets trading floor. Route: use "
         "the Genie space for exposure / gross notional / net exposure / unrealized PnL roll-ups and for "
         "which clients hold an instrument; use get_client_positions for a single named client's book; "
         "use compute_shock_pnl for the PnL impact of a percentage price shock. Amounts CAD. Be concise."))
tool(pa.supervisor_agent_id, "portfolio-genie", sa.Tool(tool_type="genie_space", name="portfolio_exposure_genie",
     description="Structured exposure/notional/PnL analytics for the Portfolio desk.",
     genie_space=sa.GenieSpace(id=PORTFOLIO_SPACE)))
tool(pa.supervisor_agent_id, "get-client-positions", sa.Tool(tool_type="uc_function", name="get_client_positions",
     description="Return all positions for a given client_id (e.g. CL-AC).",
     uc_function=sa.UcFunction(name=f"{CATALOG}.cm_portfolio_gold.get_client_positions")))
tool(pa.supervisor_agent_id, "compute-shock-pnl", sa.Tool(tool_type="uc_function", name="compute_shock_pnl",
     description="Linear PnL impact (CAD) of a percentage price shock on a client position.",
     uc_function=sa.UcFunction(name=f"{CATALOG}.cm_portfolio_gold.compute_shock_pnl")))
handoff["portfolio"] = {"sid": pa.supervisor_agent_id, "endpoint": pa.endpoint_name}

# ---------- Desk B · B2: Research Desk Agent ----------
print("=== Research Desk Agent ===")
ra = mk("Research Desk Agent",
        "Research & Filings desk agent: analyst house views + structured filing facts.",
        ("You are the Research & Filings desk agent. Use the Research KA for qualitative house views and "
         "risk commentary; use get_filing_facts for exact structured facts from a client's filings. Prefer "
         "get_filing_facts when the user asks for a specific number or policy. Cite sources. Client ids look like CL-AC."))
tool(ra.supervisor_agent_id, "research-ka", sa.Tool(tool_type="knowledge_assistant", name="research_filings_ka",
     description="Analyst research house-views, hedging strategy, and risk commentary.",
     knowledge_assistant=sa.KnowledgeAssistant(knowledge_assistant_id=handoff["ka_id"], serving_endpoint_name=handoff["ka_endpoint"])))
tool(ra.supervisor_agent_id, "get-filing-facts", sa.Tool(tool_type="uc_function", name="get_filing_facts",
     description="Structured facts from a client's filings (hedge policy, ratios, notionals, covenants).",
     uc_function=sa.UcFunction(name=f"{CATALOG}.cm_research_gold.get_filing_facts")))
handoff["research"] = {"sid": ra.supervisor_agent_id, "endpoint": ra.endpoint_name}

# ---------- Desk C · C2: Market Intel Desk Agent ----------
print("=== Market Intel Desk Agent ===")
ma = mk("Market Intel Desk Agent",
        "Market Intelligence desk agent: news sentiment / adverse media and client signal exposure.",
        ("You are the Market Intelligence desk agent. Use the Genie space for news, sentiment/adverse-media "
         "questions and to find which clients are exposed to a market event. Use get_client_signals for a "
         "single named client's news-signal exposure. Client ids look like CL-AC. Be concise."))
tool(ma.supervisor_agent_id, "market-genie", sa.Tool(tool_type="genie_space", name="market_intel_genie",
     description="News sentiment, adverse media, and client signal exposure analytics.",
     genie_space=sa.GenieSpace(id=MARKET_SPACE)))
tool(ma.supervisor_agent_id, "get-client-signals", sa.Tool(tool_type="uc_function", name="get_client_signals",
     description="News events a client is exposed to, with sentiment and position/PnL.",
     uc_function=sa.UcFunction(name=f"{CATALOG}.cm_market_gold.get_client_signals")))
handoff["market"] = {"sid": ma.supervisor_agent_id, "endpoint": ma.endpoint_name}

json.dump(handoff, open("/Users/elmer.cecilio/Claude_Projects/cibc-cm-desks-workshop/dryrun_fevm/handoff_ids.json","w"), indent=2)
print("\n=== HANDOFF ===\n", json.dumps(handoff, indent=2))

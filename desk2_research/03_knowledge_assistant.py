#!/usr/bin/env python3
"""
Desk 2 · D2.3 — Research Knowledge Assistant (vectorized).

KA over cm_research_gold.research_docs. A Delta table is a valid `file_table` source (content col
+ _metadata struct + CDF) — NO Volume staging. Requires databricks-sdk >= 0.133.
Genie Code prompt equivalent: RUNBOOK D2.3 (databricks-agent-bricks skill).
"""
from databricks.sdk import WorkspaceClient
from databricks.sdk.service import knowledgeassistants as ka

import argparse
_p = argparse.ArgumentParser()
_p.add_argument("--profile", default="pbb-demo")
_p.add_argument("--catalog", default="ec_demo_workspace")
_a = _p.parse_args()
CATALOG = _a.catalog
w = WorkspaceClient(profile=_a.profile)

assistant = w.knowledge_assistants.create_knowledge_assistant(
    ka.KnowledgeAssistant(
        display_name="Research & Filings KA",
        description="Analyst research house-views and risk commentary for capital-markets clients.",
        instructions=(
            "Answer questions about the desk's house view, hedging strategy, risks, and outlook for "
            "capital-markets clients (e.g. Air Canada fuel hedging). Ground every answer in the "
            "research corpus and cite the source note. If the corpus does not cover it, say so."
        ),
    )
)
print("created KA:", assistant.id, "name:", assistant.name, "endpoint:", assistant.endpoint_name)

src = w.knowledge_assistants.create_knowledge_source(
    parent=assistant.name,
    knowledge_source=ka.KnowledgeSource(
        display_name="Analyst research corpus",
        description="Initiations, quarterly updates, flash notes, risk notes, sector pieces per client.",
        source_type="file_table",
        file_table=ka.FileTableSpec(
            table_name=f"{CATALOG}.cm_research_gold.research_docs", file_col="content"),
    ),
)
print("source:", src.id, "state:", src.state)
# Kick a sync (endpoint is READY fast; vector index sync runs in background)
try:
    w.knowledge_assistants.sync_knowledge_sources(name=assistant.name)
    print("sync requested")
except Exception as e:
    print("sync note:", e)
print("KA_ID", assistant.id)
print("KA_ENDPOINT", assistant.endpoint_name)

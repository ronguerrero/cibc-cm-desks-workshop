# Desk 2 — Research & Filings

The unstructured / RAG desk. Vectorizes analyst research into a Knowledge Assistant and pairs it
with a deterministic filing-facts function. **Lead surface: Genie Code (Path A)**; notebooks below
are the Path-B equivalent.

| Step | File | Builds | Live IDs (pbb-demo) |
|---|---|---|---|
| D2.1 | `01_research_corpus.py` | `cm_research_gold.research_docs` (KA-shaped, certified, CDF) | — |
| D2.2 | `02_uc_function.py` | `get_filing_facts(p_client_id, p_fact_type)` | — |
| D2.3 | `03_knowledge_assistant.py` | Research & Filings KA | `ka-a462749b-endpoint` |
| D2.5 | `05_mcp.md` | managed MCP + public SEC EDGAR MCP notes | — |
| D2.6 | `06_desk_agent.py` | **Research Desk Agent** (MAS: KA + get_filing_facts) | `mas-ac2a8b1e-endpoint` |

**Validated live (2026-09-03):** the desk agent's `get_filing_facts` route returned Air Canada's
real **75% / 50% / 25%** jet-fuel hedge policy with source pages. KA vector index sync completes in
the background (45/45 files ingested); the KA retrieval route lights up once the index is live.

Requirements: D2.1/D2.2 run on any pbb-demo compute; D2.3/D2.6 need `databricks-sdk>=0.133`
(`w.knowledge_assistants`, `w.supervisor_agents`). **KA finding:** a Delta table with `content` +
`_metadata` struct + CDF is a valid `file_table` source — no Volume staging.

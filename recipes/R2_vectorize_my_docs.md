# R2 — "Here are my documents. How do I vectorize them and query them?"

Two routes. Route A (managed KA) is the easy path; route B (raw Vector Search) is the DIY path.

## Route A — Knowledge Assistant over a Delta table (recommended, no Volume staging)
A Delta table is a valid KA `file_table` source if it has a **`content` column + a `_metadata`
STRUCT + Change Data Feed**. No files-in-a-Volume needed.

1. Shape the table (proven in `desk2_research/01_research_corpus.py`):
```sql
CREATE OR REPLACE TABLE <cat>.<schema>.my_docs
TBLPROPERTIES (delta.enableChangeDataFeed = true) AS
SELECT id,
       concat('# ', title, '\n\n', body) AS content,
       named_struct('file_path', concat('/docs/', id, '.md'), 'file_name', concat(id, '.md'),
         'file_size', CAST(length(body) AS BIGINT),
         'file_modification_time', CAST(updated_at AS TIMESTAMP)) AS _metadata
FROM <source>;
```
2. Create the KA + source (SDK ≥ 0.133):
```python
from databricks.sdk import WorkspaceClient
from databricks.sdk.service import knowledgeassistants as ka
w = WorkspaceClient(profile="pbb-demo")
a = w.knowledge_assistants.create_knowledge_assistant(ka.KnowledgeAssistant(
    display_name="My KA", description="...", instructions="Answer from the corpus and cite."))
w.knowledge_assistants.create_knowledge_source(parent=a.name, knowledge_source=ka.KnowledgeSource(
    display_name="My docs", source_type="file_table",
    file_table=ka.FileTableSpec(table_name="<cat>.<schema>.my_docs", file_col="content")))
w.knowledge_assistants.sync_knowledge_sources(name=a.name)
```
**Timing:** endpoint is READY fast; the vector index syncs in the background (state
`KNOWLEDGE_SOURCE_STATE_UPDATING` → `UPDATED`) — minutes for a small corpus. Query only errors with
"Vector index … is not ready" until it flips to UPDATED; then it returns grounded answers.

## Route B — raw Vector Search (DIY, full control)
Chunk → embed (`databricks-gte-large-en`) → `DELTA_SYNC` index → query. Use when you want your own
chunking/embedding or to expose the index as a tool directly. (Managed VS endpoint + index; see the
`databricks-vector-search` skill / docs.)

## ✓ Validation
Ask the KA a question only the docs answer. In this build: "analyst view on Air Canada fuel hedging"
→ grounded answer with the desk recommendation, once the index reached UPDATED.

## Caveat
A KA vector index is a snapshot and does **not** enforce per-caller UC row filters. If the source
table has RLS, a restricted user can still retrieve indexed text. Sync the KA from a row-filtered
source, or scope a KA per audience.

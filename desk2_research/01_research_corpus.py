# Databricks notebook source
# MAGIC %md
# MAGIC # Desk 2 · D2.1 — Research corpus (KA-shaped) + certify
# MAGIC Builds `cm_research_gold.research_docs` from the seed's `<prefix>_silver.research_notes` in the
# MAGIC **Knowledge Assistant file-table contract**: a `content` column + a `_metadata` STRUCT
# MAGIC (file_path, file_name, file_size, file_modification_time) + Change Data Feed enabled.
# MAGIC A Delta table in this shape is a valid KA `file_table` source — **no Volume staging**.
# MAGIC
# MAGIC **Path B (code).** Genie Code prompt equivalent: `PROMPT_RUNBOOK.md` (D2.1).

# COMMAND ----------

dbutils.widgets.text("catalog", "ec_demo_workspace")
dbutils.widgets.text("schema_prefix", "cibc_cm")  # seed prefix from data/01_generate_seed.py — must match
CATALOG = dbutils.widgets.get("catalog")
PFX     = dbutils.widgets.get("schema_prefix")
SILVER  = f"{CATALOG}.{PFX}_silver"
spark.sql(f"""CREATE SCHEMA IF NOT EXISTS {CATALOG}.cm_research_gold
COMMENT 'Research & Filings desk — governed data product (analyst research corpus + filing facts)'""")

# COMMAND ----------

spark.sql(f"""
CREATE OR REPLACE TABLE {CATALOG}.cm_research_gold.research_docs
COMMENT 'Analyst research corpus shaped for Knowledge Assistant ingestion: content + _metadata struct, CDF enabled.'
TBLPROPERTIES (delta.enableChangeDataFeed = true)
AS
SELECT note_id, client_id, ticker, author_desk, doc_type, published_date, title, tags,
       concat('# ', title, '\\n\\n', body) AS content,
       named_struct(
         'file_path', concat('/research/', note_id, '.md'),
         'file_name', concat(note_id, '.md'),
         'file_size', CAST(length(concat('# ', title, '\\n\\n', body)) AS BIGINT),
         'file_modification_time', CAST(published_date AS TIMESTAMP)
       ) AS _metadata
FROM {SILVER}.research_notes
""")
spark.sql(f"ALTER TABLE {CATALOG}.cm_research_gold.research_docs SET TAGS ('system.certification_status' = 'certified')")

# COMMAND ----------

# MAGIC %md ## Validate — content present, all clients covered

# COMMAND ----------

r = spark.sql(f"SELECT count(*) n, count(DISTINCT client_id) c, min(length(content)) mn FROM {CATALOG}.cm_research_gold.research_docs").collect()[0]
assert r.n == 45 and r.c == 9 and r.mn > 100, r
print(f"OK — {r.n} research docs, {r.c} clients, min content {r.mn} chars, CDF on, certified.")

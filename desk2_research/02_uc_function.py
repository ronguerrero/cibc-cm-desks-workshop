# Databricks notebook source
# MAGIC %md
# MAGIC # Desk 2 · D2.2 — get_filing_facts UC function
# MAGIC Structured facts extracted from client filings (hedge policy, ratios, notionals, covenants).
# MAGIC Deterministic companion to the KA — use it when the user asks for a specific number/policy.
# MAGIC
# MAGIC **Path B (code).** Genie Code prompt equivalent: `PROMPT_RUNBOOK.md` (D2.2).

# COMMAND ----------

dbutils.widgets.text("catalog", "ec_demo_workspace")
dbutils.widgets.text("schema_prefix", "cibc_cm")  # seed prefix from data/01_generate_seed.py — must match
CATALOG = dbutils.widgets.get("catalog")
PFX     = dbutils.widgets.get("schema_prefix")
SILVER  = f"{CATALOG}.{PFX}_silver"
spark.sql(f"""
CREATE OR REPLACE FUNCTION {CATALOG}.cm_research_gold.get_filing_facts(
  p_client_id STRING, p_fact_type STRING DEFAULT NULL)
RETURNS TABLE (client_id STRING, fact_type STRING, fact_value STRING, unit STRING, source_page INT, file STRING)
COMMENT 'Return structured facts extracted from a client filings (e.g. CL-AC). fact_type in hedge_policy, hedge_ratio, derivative_notional, commodity_exposure, fx_exposure, rate_exposure, covenant, risk_factor. Pass p_fact_type to filter, or NULL for all.'
RETURN SELECT client_id, fact_type, fact_value, unit, source_page, file
       FROM {SILVER}.filing_facts
       WHERE client_id = p_client_id
         AND (p_fact_type IS NULL OR fact_type = p_fact_type)
""")

# COMMAND ----------

# MAGIC %md ## Validate — AC hedge policy facts present (the 75% jet-fuel hero)

# COMMAND ----------

n = spark.sql(f"SELECT count(*) c FROM {CATALOG}.cm_research_gold.get_filing_facts('CL-AC','hedge_policy')").collect()[0].c
assert n > 0, "expected AC hedge_policy facts"
print(f"OK — AC has {n} hedge_policy facts (fuel hedging up to 75% policy).")

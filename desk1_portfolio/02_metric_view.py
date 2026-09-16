# Databricks notebook source
# MAGIC %md
# MAGIC # Desk 1 · D1.2 — Exposure metric view (semantic layer)
# MAGIC The governed semantic layer for the Portfolio desk. Named business measures + dimensions
# MAGIC feed the **Genie Ontology / OntoRank** so Genie One can discover and rank this desk's product.
# MAGIC
# MAGIC **Path B (code).** Genie Code prompt equivalent in `PROMPT_RUNBOOK.md` (D1.2).

# COMMAND ----------

dbutils.widgets.text("catalog", "ec_demo_workspace")
dbutils.widgets.text("schema_prefix", "cibc_cm")  # seed prefix from data/01_generate_seed.py — must match
CATALOG = dbutils.widgets.get("catalog")
spark.sql(f"""CREATE SCHEMA IF NOT EXISTS {CATALOG}.cm_portfolio_metrics
COMMENT 'Portfolio & Exposure desk — certified semantic layer (metric views)'""")

# COMMAND ----------

spark.sql(f"""
CREATE OR REPLACE VIEW {CATALOG}.cm_portfolio_metrics.exposure_kpis
COMMENT 'Certified exposure KPIs by client, ticker, sector, desk, book, currency, asset class, and coverage officer. Query with MEASURE().'
WITH METRICS
LANGUAGE YAML
AS $$
version: 0.1
source: {CATALOG}.cm_portfolio_gold.positions
dimensions:
  - name: Client
    expr: client_name
  - name: Ticker
    expr: ticker
  - name: Sector
    expr: sector
  - name: Desk
    expr: desk
  - name: Book
    expr: book
  - name: Currency
    expr: native_ccy
  - name: Asset Class
    expr: asset_class
  - name: Coverage Officer
    expr: coverage_officer
measures:
  - name: Gross Notional CAD
    expr: SUM(gross_notional_cad)
  - name: Net Exposure CAD
    expr: SUM(gross_notional_cad * CASE WHEN net_qty < 0 THEN -1 ELSE 1 END)
  - name: Unrealized PnL CAD
    expr: SUM(unrealized_pnl_cad)
  - name: Position Count
    expr: COUNT(1)
  - name: Client Count
    expr: COUNT(DISTINCT client_id)
$$
""")

spark.sql(f"ALTER VIEW {CATALOG}.cm_portfolio_metrics.exposure_kpis SET TAGS ('system.certification_status' = 'certified')")

# COMMAND ----------

# MAGIC %md ## Validate — MEASURE() ties to the raw gold aggregate

# COMMAND ----------

mv = spark.sql(f"""
SELECT round(MEASURE(`Gross Notional CAD`)) g, MEASURE(`Position Count`) p, MEASURE(`Client Count`) c
FROM {CATALOG}.cm_portfolio_metrics.exposure_kpis
""").collect()[0]
raw = spark.sql(f"SELECT round(sum(gross_notional_cad)) g, count(*) p FROM {CATALOG}.cm_portfolio_gold.positions").collect()[0]
assert mv.g == raw.g and mv.p == raw.p, f"metric view mismatch: {mv} vs {raw}"
print(f"OK — metric view ties: gross {mv.g}, positions {mv.p}, clients {mv.c}")

# COMMAND ----------

# MAGIC %md Top sectors by gross notional (Energy should lead ~$2.78B)

# COMMAND ----------

display(spark.sql(f"""
SELECT `Sector`, round(MEASURE(`Gross Notional CAD`)) gross_notional
FROM {CATALOG}.cm_portfolio_metrics.exposure_kpis GROUP BY `Sector` ORDER BY gross_notional DESC
"""))

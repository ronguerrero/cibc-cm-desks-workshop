# Databricks notebook source
# MAGIC %md
# MAGIC # Desk 1 · D1.3 — UC function tools
# MAGIC Governed, callable tools for the desk agent. SQL table functions (reliable on serverless;
# MAGIC no scalar-subquery planner issues). Params are `p_`-prefixed to avoid the UC SQL-UDF
# MAGIC column-shadow trap (an unprefixed `client_id` param gets shadowed by the column → returns all rows).
# MAGIC
# MAGIC **Path B (code).** Genie Code prompt equivalent in `PROMPT_RUNBOOK.md` (D1.3).

# COMMAND ----------

dbutils.widgets.text("catalog", "ec_demo_workspace")
CATALOG = dbutils.widgets.get("catalog")

spark.sql(f"""
CREATE OR REPLACE FUNCTION {CATALOG}.cm_portfolio_gold.get_client_positions(p_client_id STRING)
RETURNS TABLE (client_id STRING, client_name STRING, ticker STRING, instrument_id STRING,
               asset_class STRING, desk STRING, book STRING, net_qty DOUBLE,
               gross_notional_cad DOUBLE, unrealized_pnl_cad DOUBLE)
COMMENT 'Return all positions for a given client_id (e.g. CL-AC for Air Canada): instrument, asset class, desk, book, net quantity, gross notional (CAD) and unrealized PnL (CAD).'
RETURN SELECT client_id, client_name, ticker, instrument_id, asset_class, desk, book,
              net_qty, gross_notional_cad, unrealized_pnl_cad
       FROM {CATALOG}.cm_portfolio_gold.positions
       WHERE client_id = p_client_id
""")

# COMMAND ----------

spark.sql(f"""
CREATE OR REPLACE FUNCTION {CATALOG}.cm_portfolio_gold.compute_shock_pnl(
  p_client_id STRING, p_instrument_id STRING, p_shock_pct DOUBLE)
RETURNS TABLE (client_id STRING, ticker STRING, instrument_id STRING, net_qty DOUBLE,
               gross_notional_cad DOUBLE, shock_pct DOUBLE, pnl_impact_cad DOUBLE)
COMMENT 'Estimate linear PnL impact (CAD) on a client position in an instrument for a percentage price shock (e.g. -10 for a 10 percent drop). A long position (positive net_qty) loses on a negative shock.'
RETURN SELECT client_id, ticker, instrument_id, net_qty, gross_notional_cad,
              p_shock_pct AS shock_pct,
              (CASE WHEN net_qty < 0 THEN -1 ELSE 1 END) * gross_notional_cad * (p_shock_pct/100.0) AS pnl_impact_cad
       FROM {CATALOG}.cm_portfolio_gold.positions
       WHERE client_id = p_client_id AND instrument_id = p_instrument_id
""")

# COMMAND ----------

# MAGIC %md ## Validate — AC book + hero PnL (WTI -10% is a loss for AC's long)

# COMMAND ----------

n = spark.sql(f"SELECT count(*) c FROM {CATALOG}.cm_portfolio_gold.get_client_positions('CL-AC')").collect()[0].c
assert n == 8, f"expected 8 AC positions, got {n}"

pnl = spark.sql(f"SELECT round(pnl_impact_cad) v FROM {CATALOG}.cm_portfolio_gold.compute_shock_pnl('CL-AC','WTI',-10)").collect()[0].v
assert pnl < 0, f"HERO BROKEN: AC long WTI should lose on -10% shock, got {pnl}"
print(f"OK — AC has {n} positions; WTI -10% shock => {pnl} CAD (loss, hero holds)")

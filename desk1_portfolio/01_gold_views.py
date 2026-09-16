# Databricks notebook source
# MAGIC %md
# MAGIC # Desk 1 · D1.1 — Portfolio gold data product
# MAGIC Builds the Portfolio & Exposure desk's **certified** gold views from the seed's `<prefix>_silver`.
# MAGIC This is the desk's owned, governed data product boundary.
# MAGIC
# MAGIC **Path B (code).** The equivalent Genie Code prompt is in `PROMPT_RUNBOOK.md` (D1.1).

# COMMAND ----------

dbutils.widgets.text("catalog", "ec_demo_workspace")
dbutils.widgets.text("schema_prefix", "cibc_cm")  # seed prefix from data/01_generate_seed.py — must match
CATALOG = dbutils.widgets.get("catalog")
PFX     = dbutils.widgets.get("schema_prefix")
SILVER  = f"{CATALOG}.{PFX}_silver"
GOLD    = f"{CATALOG}.{PFX}_gold"
spark.sql(f"""CREATE SCHEMA IF NOT EXISTS {CATALOG}.cm_portfolio_gold
COMMENT 'Portfolio & Exposure desk — governed data product (positions, exposures)'""")

# COMMAND ----------

spark.sql(f"""
CREATE OR REPLACE VIEW {CATALOG}.cm_portfolio_gold.positions
COMMENT 'Certified position-level exposures per client/instrument with sector, desk, book, currency, coverage officer, gross notional, and unrealized PnL (CAD).'
AS
SELECT p.snapshot_date, p.client_id, c.legal_name AS client_name, c.ticker, c.sector,
       c.country, c.coverage_officer, p.instrument_id, i.asset_class,
       i.description AS instrument_desc, i.native_ccy, p.desk, p.book,
       p.net_qty, p.avg_entry_price, p.spot_price,
       p.gross_notional_cad, p.unrealized_pnl_cad
FROM {SILVER}.positions p
JOIN {SILVER}.clients c     ON p.client_id = c.client_id
JOIN {SILVER}.instruments i ON p.instrument_id = i.instrument_id
""")

spark.sql(f"""
CREATE OR REPLACE VIEW {CATALOG}.cm_portfolio_gold.clients
COMMENT 'Certified client/issuer master: ticker, sector, country, primary desk, credit rating, coverage officer (chinese-wall boundary).'
AS
SELECT client_id, ticker, legal_name, sector, country, isda_active,
       primary_desk, credit_rating, coverage_officer
FROM {SILVER}.clients
""")

# COMMAND ----------

# Certify (authority signal for Genie One discovery + OntoRank)
for v in ["positions", "clients"]:
    spark.sql(f"ALTER VIEW {CATALOG}.cm_portfolio_gold.{v} SET TAGS ('system.certification_status' = 'certified')")

# COMMAND ----------

# MAGIC %md ## Validate — counts tie to silver, certification present

# COMMAND ----------

gp = spark.table(f"{CATALOG}.cm_portfolio_gold.positions").count()
sp = spark.table(f"{SILVER}.positions").count()
assert gp == sp, f"positions mismatch: gold {gp} vs silver {sp}"
assert spark.table(f"{CATALOG}.cm_portfolio_gold.clients").count() == 9
print(f"OK — positions tie ({gp}={sp}), 9 clients, views certified.")

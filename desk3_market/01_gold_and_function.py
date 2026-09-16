# Databricks notebook source
# MAGIC %md
# MAGIC # Desk 3 · D3.1 + D3.3 — Market Intel gold + signal function
# MAGIC Certified news + signal-match views and the `get_client_signals` UC function.
# MAGIC
# MAGIC **Path B (code).** Genie Code prompt equivalents: `PROMPT_RUNBOOK.md` (D3.1, D3.3).

# COMMAND ----------

dbutils.widgets.text("catalog", "ec_demo_workspace")
dbutils.widgets.text("schema_prefix", "cibc_cm")  # seed prefix from data/01_generate_seed.py — must match
CATALOG = dbutils.widgets.get("catalog")
PFX     = dbutils.widgets.get("schema_prefix")
SILVER  = f"{CATALOG}.{PFX}_silver"
GOLD    = f"{CATALOG}.{PFX}_gold"
spark.sql(f"""CREATE SCHEMA IF NOT EXISTS {CATALOG}.cm_market_gold
COMMENT 'Market Intelligence desk — governed data product (tagged news + client signal matches)'""")

# COMMAND ----------

spark.sql(f"""
CREATE OR REPLACE VIEW {CATALOG}.cm_market_gold.news_events
COMMENT 'Certified tagged market-news events: headline, source, sentiment, asset classes, entities, themes.'
AS SELECT event_id, headline, body, source, source_url, published_at,
          sentiment_label, asset_classes, entities, themes
   FROM {SILVER}.news_events_tagged
""")

spark.sql(f"""
CREATE OR REPLACE VIEW {CATALOG}.cm_market_gold.signal_matches
COMMENT 'Certified client exposure to news events: which client, via which asset class, position and unrealized PnL (CAD), with the headline and sentiment.'
AS SELECT m.event_id, m.client_id, c.legal_name AS client_name, c.ticker,
          m.matched_asset_class, m.client_net_qty_in_asset, m.client_unrealized_pnl_cad,
          n.headline, n.sentiment_label, n.published_at, n.source
   FROM {GOLD}.client_signal_matches m
   JOIN {SILVER}.clients c            ON m.client_id = c.client_id
   JOIN {SILVER}.news_events_tagged n ON m.event_id = n.event_id
""")

for v in ["news_events", "signal_matches"]:
    spark.sql(f"ALTER VIEW {CATALOG}.cm_market_gold.{v} SET TAGS ('system.certification_status' = 'certified')")

# COMMAND ----------

spark.sql(f"""
CREATE OR REPLACE FUNCTION {CATALOG}.cm_market_gold.get_client_signals(p_client_id STRING)
RETURNS TABLE (client_id STRING, client_name STRING, matched_asset_class STRING,
               headline STRING, sentiment_label STRING, published_at TIMESTAMP,
               client_net_qty_in_asset DOUBLE, client_unrealized_pnl_cad DOUBLE)
COMMENT 'Return market-news events a client (e.g. CL-AC) is exposed to, with matched asset class, headline, sentiment, and the client position/PnL affected.'
RETURN SELECT client_id, client_name, matched_asset_class, headline, sentiment_label,
              published_at, client_net_qty_in_asset, client_unrealized_pnl_cad
       FROM {CATALOG}.cm_market_gold.signal_matches
       WHERE client_id = p_client_id
""")

# COMMAND ----------

# MAGIC %md ## Validate — AC exposed to oil (WTI) news

# COMMAND ----------

n = spark.sql(f"SELECT count(*) c FROM {CATALOG}.cm_market_gold.get_client_signals('CL-AC') WHERE matched_asset_class='WTI'").collect()[0].c
assert n > 0, "expected AC WTI news exposure"
print(f"OK — AC exposed to {n} WTI news signals.")

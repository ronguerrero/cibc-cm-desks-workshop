# Databricks notebook source
# MAGIC %md
# MAGIC # Phase 3 · Governance — ABAC column mask + chinese-wall RLS
# MAGIC Governance that **travels with the data** and flows through Genie + the desk agents.
# MAGIC Teaches two patterns:
# MAGIC 1. **Native ABAC** on tables — `SET MASK` / `SET ROW FILTER` (clients, research_docs).
# MAGIC 2. **Secure-view RLS** — the row-filter function baked into the view WHERE (positions, signal_matches).
# MAGIC
# MAGIC Path B (code). Genie Code prompt equivalents in `PROMPT_RUNBOOK.md` (S2).

# COMMAND ----------

dbutils.widgets.text("catalog", "ec_demo_workspace")
dbutils.widgets.text("schema_prefix", "cibc_cm")  # seed prefix from data/01_generate_seed.py — must match
CATALOG = dbutils.widgets.get("catalog")
PFX     = dbutils.widgets.get("schema_prefix")
SILVER  = f"{CATALOG}.{PFX}_silver"
GOLD    = f"{CATALOG}.{PFX}_gold"
spark.sql(f"""CREATE SCHEMA IF NOT EXISTS {CATALOG}.cm_governance
COMMENT 'Shared governance layer for the CM desks — ABAC masks and chinese-wall row filters'""")

# COMMAND ----------

# MAGIC %md ## Column mask — credit_rating (MNPI-sensitive) unless caller in cm_privileged

# COMMAND ----------

spark.sql(f"""
CREATE OR REPLACE FUNCTION {CATALOG}.cm_governance.mask_rating(rating STRING)
RETURNS STRING
COMMENT 'Mask credit rating unless the caller is a member of cm_privileged.'
RETURN CASE WHEN is_account_group_member('cm_privileged') THEN rating ELSE '***' END
""")
# clients must be a TABLE for SET MASK (masks are table-level). Built from silver.
spark.sql(f"DROP VIEW IF EXISTS {CATALOG}.cm_portfolio_gold.clients")
spark.sql(f"""
CREATE TABLE IF NOT EXISTS {CATALOG}.cm_portfolio_gold.clients
COMMENT 'Certified client/issuer master with ABAC: credit_rating masked; chinese-wall row filter.'
AS SELECT client_id, ticker, legal_name, sector, country, isda_active, primary_desk, credit_rating, coverage_officer
   FROM {SILVER}.clients
""")
spark.sql(f"ALTER TABLE {CATALOG}.cm_portfolio_gold.clients ALTER COLUMN credit_rating SET MASK {CATALOG}.cm_governance.mask_rating")

# COMMAND ----------

# MAGIC %md ## Chinese-wall — coverage ACL + row-filter functions

# COMMAND ----------

spark.sql(f"""CREATE TABLE IF NOT EXISTS {CATALOG}.cm_governance.coverage_acl (user_email STRING, coverage_officer STRING)
COMMENT 'Maps a user to the coverage officer(s) whose clients they may see. Empty + not in cm_all_access = sees nothing.'""")
# Seed: workshop owner sees all (acts as desk head). Real desk users get one officer each.
spark.sql(f"DELETE FROM {CATALOG}.cm_governance.coverage_acl WHERE user_email = current_user()")
spark.sql(f"""INSERT INTO {CATALOG}.cm_governance.coverage_acl
  SELECT current_user(), officer FROM (VALUES ('Sofia Martins'),('David Chen'),('Priya Nair')) t(officer)""")

spark.sql(f"""
CREATE OR REPLACE FUNCTION {CATALOG}.cm_governance.coverage_wall(officer STRING)
RETURNS BOOLEAN
RETURN is_account_group_member('cm_all_access')
    OR officer IN (SELECT coverage_officer FROM {CATALOG}.cm_governance.coverage_acl WHERE user_email = current_user())
""")
spark.sql(f"""
CREATE OR REPLACE FUNCTION {CATALOG}.cm_governance.coverage_wall_client(client_id STRING)
RETURNS BOOLEAN
RETURN is_account_group_member('cm_all_access')
    OR client_id IN (SELECT cl.client_id FROM {SILVER}.clients cl
                     JOIN {CATALOG}.cm_governance.coverage_acl a ON a.coverage_officer = cl.coverage_officer
                     WHERE a.user_email = current_user())
""")

# COMMAND ----------

# Native SET ROW FILTER on tables
spark.sql(f"ALTER TABLE {CATALOG}.cm_portfolio_gold.clients SET ROW FILTER {CATALOG}.cm_governance.coverage_wall ON (coverage_officer)")
spark.sql(f"ALTER TABLE {CATALOG}.cm_research_gold.research_docs SET ROW FILTER {CATALOG}.cm_governance.coverage_wall_client ON (client_id)")
for v in ["clients"]:
    spark.sql(f"ALTER TABLE {CATALOG}.cm_portfolio_gold.{v} SET TAGS ('system.certification_status' = 'certified')")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Secure-view RLS — filter baked into positions & signal_matches views
# MAGIC Views can't take SET ROW FILTER, so the wall lives in the WHERE. The metric view + UC functions
# MAGIC that source these views inherit the filter automatically.

# COMMAND ----------

spark.sql(f"""
CREATE OR REPLACE VIEW {CATALOG}.cm_portfolio_gold.positions
COMMENT 'Certified position-level exposures (CAD). Chinese-wall via cm_governance.coverage_wall.'
AS SELECT p.snapshot_date, p.client_id, c.legal_name AS client_name, c.ticker, c.sector,
          c.country, c.coverage_officer, p.instrument_id, i.asset_class,
          i.description AS instrument_desc, i.native_ccy, p.desk, p.book,
          p.net_qty, p.avg_entry_price, p.spot_price, p.gross_notional_cad, p.unrealized_pnl_cad
   FROM {SILVER}.positions p
   JOIN {SILVER}.clients c     ON p.client_id = c.client_id
   JOIN {SILVER}.instruments i ON p.instrument_id = i.instrument_id
   WHERE {CATALOG}.cm_governance.coverage_wall(c.coverage_officer)
""")
spark.sql(f"ALTER VIEW {CATALOG}.cm_portfolio_gold.positions SET TAGS ('system.certification_status' = 'certified')")

spark.sql(f"""
CREATE OR REPLACE VIEW {CATALOG}.cm_market_gold.signal_matches
COMMENT 'Certified client exposure to news events (CAD). Chinese-wall via cm_governance.coverage_wall_client.'
AS SELECT m.event_id, m.client_id, c.legal_name AS client_name, c.ticker,
          m.matched_asset_class, m.client_net_qty_in_asset, m.client_unrealized_pnl_cad,
          n.headline, n.sentiment_label, n.published_at, n.source
   FROM {GOLD}.client_signal_matches m
   JOIN {SILVER}.clients c            ON m.client_id = c.client_id
   JOIN {SILVER}.news_events_tagged n ON m.event_id = n.event_id
   WHERE {CATALOG}.cm_governance.coverage_wall_client(m.client_id)
""")
spark.sql(f"ALTER VIEW {CATALOG}.cm_market_gold.signal_matches SET TAGS ('system.certification_status' = 'certified')")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Validate — restrict to one officer, confirm the wall, restore
# MAGIC Two-login reveal: a user mapped to only 'Sofia Martins' sees ONLY AC.TO + MG.TO across clients,
# MAGIC positions, research_docs, and signal_matches. Verified live 2026-09-03.

# COMMAND ----------

# demo of restriction (owner temporarily scoped to Sofia)
spark.sql(f"DELETE FROM {CATALOG}.cm_governance.coverage_acl WHERE user_email=current_user() AND coverage_officer IN ('David Chen','Priya Nair')")
seen = [r.ticker for r in spark.sql(f"SELECT DISTINCT ticker FROM {CATALOG}.cm_portfolio_gold.clients ORDER BY ticker").collect()]
print("scoped to Sofia -> sees:", seen)
assert set(seen) == {"AC.TO", "MG.TO"}, seen
# restore full access for the workshop owner
spark.sql(f"""INSERT INTO {CATALOG}.cm_governance.coverage_acl
  SELECT current_user(), officer FROM (VALUES ('David Chen'),('Priya Nair')) t(officer)""")
print("restored full access:", spark.table(f"{CATALOG}.cm_portfolio_gold.clients").count(), "clients")

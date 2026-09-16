# Databricks notebook source
# MAGIC %md
# MAGIC # Phase 0 — Verify the CM data foundation
# MAGIC Confirms the shared capital-markets seed (reused from Bellwether) exists on `pbb-demo`
# MAGIC before any desk builds on it. Each desk builds its **own** gold data product on top of
# MAGIC `cibc_cm_silver` — this notebook just gates that the raw material is present and the hero holds.
# MAGIC
# MAGIC Catalog `ec_demo_workspace`, source schema `cibc_cm_silver` (+ `cibc_cm_gold`).

# COMMAND ----------

CATALOG = "ec_demo_workspace"

expected = {
    "cibc_cm_silver.clients": 9,
    "cibc_cm_silver.positions": 124,
    "cibc_cm_silver.trades": 626,
    "cibc_cm_silver.instruments": 22,
    "cibc_cm_silver.research_notes": 45,
    "cibc_cm_silver.filing_facts": 387,
    "cibc_cm_silver.filing_chunks": 1132,
    "cibc_cm_silver.news_events_tagged": 45,
    "cibc_cm_gold.client_signal_matches": 139,
}
for tbl, want in expected.items():
    got = spark.table(f"{CATALOG}.{tbl}").count()
    status = "OK" if got >= want else "LOW"
    print(f"[{status}] {tbl}: {got} (expected >= {want})")

# COMMAND ----------

# MAGIC %md ## Coverage officers (chinese-wall RLS boundary)

# COMMAND ----------

display(spark.sql(f"""
SELECT coverage_officer, count(*) n, concat_ws(', ', collect_list(ticker)) tickers
FROM {CATALOG}.cibc_cm_silver.clients GROUP BY coverage_officer ORDER BY coverage_officer
"""))
# Expect: David Chen (BCE/MFC/BAM), Priya Nair (SU/CNR/ABX/CVE), Sofia Martins (AC/MG)

# COMMAND ----------

# MAGIC %md ## Hero check — Air Canada is net-long oil (loses if oil drops)

# COMMAND ----------

hero = spark.sql(f"""
SELECT p.instrument_id, round(sum(p.net_qty)) net_qty
FROM {CATALOG}.cibc_cm_silver.positions p
JOIN {CATALOG}.cibc_cm_silver.clients c ON p.client_id=c.client_id
WHERE c.ticker='AC.TO' AND p.instrument_id IN ('WTI','HO')
GROUP BY p.instrument_id
""")
display(hero)
rows = {r.instrument_id: r.net_qty for r in hero.collect()}
assert rows.get("WTI", 0) > 0, "HERO BROKEN: AC should be net-long WTI"
print("HERO OK — AC net-long WTI:", rows)

# Databricks notebook source
# MAGIC %md
# MAGIC # Phase 0 · Generate the shared capital-markets seed (from scratch)
# MAGIC Self-contained, **deterministic** generator so a customer can recreate the workshop world on
# MAGIC their own workspace. No external files, no Volumes. Structured tables are pure PySpark; the
# MAGIC text tables (research notes, filing facts, news) use `ai_query` on Foundation Model APIs.
# MAGIC
# MAGIC Produces (schema `<schema_prefix>_silver` + `<schema_prefix>_gold`): clients, instruments,
# MAGIC prices, positions, trades, research_notes, filing_facts, news_events_tagged, client_signal_matches
# MAGIC — exactly what the three desks build on. Hero preserved: **Air Canada net-long WTI/HO**.
# MAGIC
# MAGIC **Idempotent** (`CREATE OR REPLACE`). **Does not touch** any schema other than `<schema_prefix>_*`.
# MAGIC Set `schema_prefix` to your own value; the built desks on pbb-demo use `cibc_cm` (do not overwrite).

# COMMAND ----------
dbutils.widgets.text("catalog", "ec_demo_workspace")
dbutils.widgets.text("schema_prefix", "cibc_cm")     # customers: use your own; DON'T clobber cibc_cm here
dbutils.widgets.text("random_seed", "1867")
dbutils.widgets.text("llm", "databricks-claude-haiku-4-5")

CATALOG = dbutils.widgets.get("catalog")
PFX     = dbutils.widgets.get("schema_prefix")
SEED    = int(dbutils.widgets.get("random_seed"))
LLM     = dbutils.widgets.get("llm")
SILVER, GOLD = f"{CATALOG}.{PFX}_silver", f"{CATALOG}.{PFX}_gold"

import datetime as dt, numpy as np
from pyspark.sql import functions as F
from pyspark.sql.types import *
RNG = np.random.default_rng(SEED)
for s in ("silver", "gold"):
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {CATALOG}.{PFX}_{s}")

# COMMAND ----------
# MAGIC %md ## 1. Clients (9) — with coverage officer (chinese-wall boundary)

# COMMAND ----------
CLIENTS = [  # id, ticker, legal_name, sector, isda, primary_desk, credit, coverage_officer
 ("CL-AC","AC.TO","Air Canada","Airlines",True,"Energy Derivatives","BBB-","Sofia Martins"),
 ("CL-MG","MG.TO","Magna International","Auto Parts",True,"Multi-asset","A-","Sofia Martins"),
 ("CL-BCE","BCE.TO","BCE Inc.","Telecom",True,"Rates & FX","BBB+","David Chen"),
 ("CL-MFC","MFC.TO","Manulife Financial","Insurance",True,"Rates/FX/Equity","A+","David Chen"),
 ("CL-BAM","BAM.TO","Brookfield Asset Management","Alternatives",True,"Multi-asset","A","David Chen"),
 ("CL-SU","SU.TO","Suncor Energy","Energy",True,"Energy Derivatives","A-","Priya Nair"),
 ("CL-CN","CNR.TO","Canadian National Railway","Industrials",True,"Multi-asset","A","Priya Nair"),
 ("CL-ABX","ABX.TO","Barrick Gold","Mining",True,"Metals & Mining","BBB+","Priya Nair"),
 ("CL-CVE","CVE.TO","Cenovus Energy","Energy",True,"Energy Derivatives","BBB","Priya Nair"),
]
clients_schema = StructType([StructField(c, t, False) for c, t in [
    ("client_id",StringType()),("ticker",StringType()),("legal_name",StringType()),
    ("sector",StringType()),("isda_active",BooleanType()),("primary_desk",StringType()),
    ("credit_rating",StringType()),("coverage_officer",StringType())]])
(spark.createDataFrame([(c[0],c[1],c[2],c[3],c[4],c[5],c[6],c[7]) for c in CLIENTS], clients_schema)
   .withColumn("country", F.lit("CA"))
   .write.mode("overwrite").option("overwriteSchema","true").saveAsTable(f"{SILVER}.clients"))
print("clients", spark.table(f"{SILVER}.clients").count())

# COMMAND ----------
# MAGIC %md ## 2. Instruments — commodities, FX, rates, credit, equity

# COMMAND ----------
INSTR = [  # id, asset_class, description, contract_size, native_ccy, vol_ann, base_price
 ("WTI","commodity","WTI Crude Oil",1000,"USD",0.32,78.50),("BRENT","commodity","Brent Crude",1000,"USD",0.30,82.30),
 ("HO","commodity","Heating Oil / Jet",42000,"USD",0.34,2.45),("NG","commodity","Henry Hub Nat Gas",10000,"USD",0.55,3.20),
 ("WCSDIFF","commodity","WCS-WTI Differential",1000,"USD",0.45,-14.50),("GOLD","commodity","COMEX Gold",100,"USD",0.18,2180.0),
 ("COPPER","commodity","COMEX Copper",25000,"USD",0.28,4.18),("HRC","commodity","Hot-Rolled Coil Steel",20,"USD",0.30,765.0),
 ("ALUM","commodity","LME Aluminum",25,"USD",0.25,2440.0),
 ("USDCAD","fx","USD/CAD spot",1,"USD",0.08,1.3550),("EURUSD","fx","EUR/USD spot",1,"EUR",0.09,1.0850),
 ("USDMXN","fx","USD/MXN spot",1,"MXN",0.13,17.20),
 ("CAD5Y","rates","CAD 5Y Swap",1,"CAD",0.15,4.05),("CAD10Y","rates","CAD 10Y Swap",1,"CAD",0.14,4.15),
 ("CAD30Y","rates","CAD 30Y Swap",1,"CAD",0.13,3.95),
 ("CDXIG","credit","CDX IG 5Y (bps)",100000,"USD",0.20,62.0),
 ("TSX","equity","S&P/TSX 60 Index",20,"CAD",0.16,1290.0),("SPX","equity","S&P 500 Index",20,"USD",0.17,5200.0),
]
FX = {"USD":1.355,"CAD":1.0,"EUR":1.47,"MXN":0.079,"CLP":0.00147,"HKD":0.173}
instr_schema = StructType([StructField(c,t,False) for c,t in [
    ("instrument_id",StringType()),("asset_class",StringType()),("description",StringType()),
    ("contract_size",IntegerType()),("native_ccy",StringType()),("vol_ann",DoubleType()),("base_price",DoubleType())]])
(spark.createDataFrame(INSTR, instr_schema)
   .withColumn("drift_ann", F.lit(0.02))
   .write.mode("overwrite").option("overwriteSchema","true").saveAsTable(f"{SILVER}.instruments"))
print("instruments", spark.table(f"{SILVER}.instruments").count())

# COMMAND ----------
# MAGIC %md ## 3. Prices — 2y daily GBM per instrument (compact)

# COMMAND ----------
days = 504
dates = [dt.date(2024,1,2) + dt.timedelta(days=int(i*1.4)) for i in range(days)]
price_rows = []
for iid, ac, desc, cs, ccy, vol, base in INSTR:
    p = base
    dc = vol/np.sqrt(252)
    for d in dates:
        p = p * (1 + RNG.normal(0.0002, dc)) if base > 0 else base + RNG.normal(0, abs(base)*dc)
        price_rows.append((iid, d, float(round(p, 4))))
(spark.createDataFrame(price_rows, StructType([
    StructField("instrument_id",StringType()),StructField("price_date",DateType()),StructField("close",DoubleType())]))
   .write.mode("overwrite").option("overwriteSchema","true").saveAsTable(f"{SILVER}.prices"))
print("prices", spark.table(f"{SILVER}.prices").count())

# COMMAND ----------
# MAGIC %md ## 4. Positions — sector-mapped book (2 books) + Air Canada hero canonicalized

# COMMAND ----------
SECTOR_INSTR = {  # sector -> instruments the client's book holds (besides shared USDCAD + rates)
 "Airlines":["WTI","HO"], "Energy":["WTI","BRENT","WCSDIFF","NG"], "Industrials":["HO","NG"],
 "Telecom":[], "Insurance":["SPX","TSX","CDXIG"], "Mining":["GOLD","COPPER"],
 "Auto Parts":["HRC","ALUM"], "Alternatives":["CDXIG","SPX"],
}
SHARED = ["USDCAD","CAD5Y","CAD10Y"]
ispec = {r[0]:(r[1],r[3],r[4],r[6]) for r in INSTR}   # id -> (asset_class, contract_size, ccy, base_price)
def notional(iid, qty):
    ac, cs, ccy, base = ispec[iid]
    fx = FX.get(ccy, 1.0)
    if ac == "commodity":  return abs(qty)*fx*abs(base)*cs
    if ac == "equity":     return abs(qty)*fx*abs(base)*20
    return abs(qty)*fx*100000                          # fx / rates / credit
DESK = {"commodity":"Commodities","fx":"FX","rates":"Rates","credit":"Credit","equity":"Equities"}
pos = []
for cid, tk, name, sector, *_ in CLIENTS:
    holds = SECTOR_INSTR.get(sector, []) + SHARED
    for iid in holds:
        ac, cs, ccy, base = ispec[iid]
        for book in ("Client Hedge","Desk Flow"):
            qty = float(round(RNG.integers(-2000, 2001) if ac in ("rates","fx","credit","equity")
                              else RNG.integers(-200, 201)))
            if qty == 0: continue
            spot = abs(base)*(1+RNG.normal(0,0.05)); entry = spot*(1+RNG.normal(0,0.03))
            gn = notional(iid, qty)
            upnl = qty*(spot-entry)*cs*FX.get(ccy,1.0) if ac in ("commodity","equity") else qty*(spot-entry)*FX.get(ccy,1.0)*100
            pos.append((dt.date(2026,2,27), cid, iid, book, DESK[ac], qty,
                        float(round(entry,4)), float(round(spot,4)), float(round(gn,2)), float(round(upnl,2))))
pos_schema = StructType([StructField(c,t) for c,t in [
    ("snapshot_date",DateType()),("client_id",StringType()),("instrument_id",StringType()),("book",StringType()),
    ("desk",StringType()),("net_qty",DoubleType()),("avg_entry_price",DoubleType()),("spot_price",DoubleType()),
    ("gross_notional_cad",DoubleType()),("unrealized_pnl_cad",DoubleType())]])
posdf = spark.createDataFrame(pos, pos_schema)
# HERO: Air Canada net-LONG WTI 150 + HO 75 (Client Hedge) — loses if oil drops
posdf = posdf.filter(~((F.col("client_id")=="CL-AC") & (F.col("instrument_id").isin("WTI","HO"))))
hero = [(dt.date(2026,2,27),"CL-AC","WTI","Client Hedge","Commodities",150.0,74.0,78.5,notional("WTI",150),-168000.0),
        (dt.date(2026,2,27),"CL-AC","HO","Client Hedge","Commodities",75.0,2.5,2.45,notional("HO",75),-195000.0)]
posdf = posdf.unionByName(spark.createDataFrame(hero, pos_schema))
posdf.write.mode("overwrite").option("overwriteSchema","true").saveAsTable(f"{SILVER}.positions")
print("positions", spark.table(f"{SILVER}.positions").count())

# COMMAND ----------
# MAGIC %md ## 5. Trades — a few per position (secondary; desks don't depend on it)

# COMMAND ----------
tr = []
for i, r in enumerate(posdf.collect()):
    for k in range(int(RNG.integers(1,4))):
        tr.append((f"T{i:04d}{k}", r.client_id, r.instrument_id, r.book,
                   float(round(r.net_qty/(k+1),2)), r.avg_entry_price,
                   (dt.date(2025,10,1)+dt.timedelta(days=int(RNG.integers(0,150)))).isoformat()))
(spark.createDataFrame(tr, "trade_id string, client_id string, instrument_id string, book string, qty double, price double, trade_date string")
   .write.mode("overwrite").option("overwriteSchema","true").saveAsTable(f"{SILVER}.trades"))
print("trades", spark.table(f"{SILVER}.trades").count())

# COMMAND ----------
# MAGIC %md
# MAGIC ## 6. Research notes — analyst house views (ai_query)
# MAGIC 5 doc types per client. Keyword-rich by design.

# COMMAND ----------
doc_types = ["Initiation","Quarterly Update","Flash Note","Risk Note","Sector Piece"]
seed_rows = [(f"{cid}-{i}", cid, tk, name, sector, dtp)
             for (cid,tk,name,sector,*_) in CLIENTS for i,dtp in enumerate(doc_types)]
seed = spark.createDataFrame(seed_rows, "note_id string, client_id string, ticker string, legal_name string, sector string, doc_type string")
notes = (seed
  .withColumn("body", F.expr(f"ai_query('{LLM}', concat('Write a concise capital-markets analyst research note (120-180 words) for ', legal_name, ' (', ticker, '), doc type: ', doc_type, '. Cover hedging strategy, key risks, and a house view. Be specific with instruments and programmes. Return ONLY the note body.'))"))
  .withColumn("title", F.concat(F.col("legal_name"), F.lit(" ("), F.col("ticker"), F.lit(") — "), F.col("doc_type")))
  .withColumn("author_desk", F.lit("Research"))
  .withColumn("published_date", F.expr("date_sub(current_date(), CAST(rand()*180 AS INT))"))
  .withColumn("tags", F.array(F.col("sector"), F.col("doc_type"))))
notes.select("note_id","client_id","ticker","author_desk","doc_type","published_date","title","body","tags") \
     .write.mode("overwrite").option("overwriteSchema","true").saveAsTable(f"{SILVER}.research_notes")
print("research_notes", spark.table(f"{SILVER}.research_notes").count())

# COMMAND ----------
# MAGIC %md
# MAGIC ## 7. Filing facts (ai_query) — with the Air Canada 75/50/25 hero hard-seeded

# COMMAND ----------
fact_types = ["hedge_policy","hedge_ratio","derivative_notional","commodity_exposure","fx_exposure","rate_exposure","covenant","risk_factor"]
fseed = [(cid, name, ft) for (cid,tk,name,sector,*_) in CLIENTS for ft in fact_types]
fdf = spark.createDataFrame(fseed, "client_id string, legal_name string, fact_type string")
facts = (fdf.withColumn("fact_value",
    F.expr(f"ai_query('{LLM}', concat('State one realistic, specific fact of type \"', fact_type, '\" that would appear in ', legal_name, \"'s annual filing (MD&A or notes). One sentence, factual, with a number where appropriate. Return only the sentence.\"))"))
  .withColumn("file", F.concat(F.lower(F.regexp_replace(F.col("legal_name"),"[^A-Za-z]","")), F.lit("_ar_2025.pdf")))
  .withColumn("source_page", F.expr("CAST(rand()*180+40 AS INT)"))
  .withColumn("unit", F.lit(None).cast("string"))
  .withColumn("extracted_at", F.current_timestamp()))
facts_final = facts.select("client_id","file","source_page","fact_type","fact_value","unit","extracted_at")
# Hard-seed the hero fact so the demo is guaranteed regardless of LLM sampling
hero_fact = spark.createDataFrame([
  ("CL-AC","aircanada_ar_2025.pdf",119,"hedge_policy",
   "Air Canada's fuel hedging policy permits hedging up to 75% of projected jet fuel purchases for the current calendar year, up to 50% for the next, and up to 25% for any year thereafter, with no minimum monthly requirement.",
   None, )], "client_id string, file string, source_page int, fact_type string, fact_value string, unit string") \
  .withColumn("extracted_at", F.current_timestamp())
facts_final.unionByName(hero_fact).write.mode("overwrite").option("overwriteSchema","true").saveAsTable(f"{SILVER}.filing_facts")
print("filing_facts", spark.table(f"{SILVER}.filing_facts").count())

# COMMAND ----------
# MAGIC %md
# MAGIC ## 8. News events (ai_query tagging) + 9. client signal matches
# MAGIC A fixed adverse/mixed headline set (oil-heavy for the hero), tagged for sentiment/asset classes.

# COMMAND ----------
HEADLINES = [
 "OPEC+ surprise output hike sends Brent down 6%","Goldman cuts Brent forecast to $70 on weak demand",
 "Crude oil price weakness deepens as inventories build","Oil services index drops 4% on capex cuts",
 "Saudi signals further supply hikes into H2","Jet fuel crack spread widens on refining glut",
 "USD/CAD slides on oil weakness and BoC dovishness","WCS-WTI heavy oil differential narrows to -$12.50 as TMX flows stabilize",
 "Air travel demand strongest since 2019","Suncor Q1 production tops estimates, free cash flow $2.1B",
 "Bank of Canada holds policy rate at 4.25%, signals Q3 cut path","US imposes 25% tariff on imported steel from select countries",
 "Gold hits record as haven demand surges","Copper rallies on China stimulus hopes",
 "Magna guides autos production down on EV slowdown","Canadian bank credit spreads tighten to cycle lows",
 "Manulife Asia new-business value beats on rate tailwinds","BCE dividend coverage in focus as capex stays elevated",
 "CN Rail volumes soft on grain, intermodal steady","Federal climate disclosure rules finalized",
]
hdf = spark.createDataFrame([(f"EV{i:03d}", h) for i,h in enumerate(HEADLINES)], "event_id string, headline string")
news = (hdf
  .withColumn("body", F.expr(f"ai_query('{LLM}', concat('Write a 2-sentence market news blurb for this headline: ', headline))"))
  .withColumn("sentiment_label", F.expr(f"ai_query('{LLM}', concat('Classify the market sentiment of this headline as exactly one of bullish, bearish, or neutral. Headline: ', headline, '. Return only the word.'))"))
  .withColumn("asset_classes", F.expr(f"split(ai_query('{LLM}', concat('Which of these asset codes are most relevant to this headline? Choose from WTI,BRENT,HO,NG,WCSDIFF,GOLD,COPPER,HRC,ALUM,USDCAD,CAD5Y,CAD10Y,CDXIG,TSX,SPX. Headline: ', headline, '. Return a comma-separated list of codes only.')), ',\\\\s*')"))
  .withColumn("entities", F.expr("array()").cast("array<string>"))
  .withColumn("themes", F.expr("array()").cast("array<string>"))
  .withColumn("source", F.lit("newswire")).withColumn("source_url", F.concat(F.lit("https://news.example.com/"), F.col("event_id")))
  .withColumn("published_at", F.expr("current_timestamp() - make_interval(0,0,0,CAST(rand()*20 AS INT))"))
  .withColumn("language", F.lit("en")).withColumn("ingested_at", F.current_timestamp()))
news.write.mode("overwrite").option("overwriteSchema","true").saveAsTable(f"{SILVER}.news_events_tagged")
print("news_events_tagged", spark.table(f"{SILVER}.news_events_tagged").count())

# COMMAND ----------
# client_signal_matches: a client is exposed to an event if it holds a position in a matched asset class
spark.sql(f"""
CREATE OR REPLACE TABLE {GOLD}.client_signal_matches AS
SELECT n2.event_id, p.client_id, n2.ac AS matched_asset_class,
       sum(p.net_qty) AS client_net_qty_in_asset,
       sum(p.unrealized_pnl_cad) AS client_unrealized_pnl_cad
FROM (SELECT event_id, explode(asset_classes) AS ac FROM {SILVER}.news_events_tagged) n2
JOIN {SILVER}.positions p ON p.instrument_id = n2.ac
GROUP BY n2.event_id, p.client_id, n2.ac
""")
print("client_signal_matches", spark.table(f"{GOLD}.client_signal_matches").count())

# COMMAND ----------
# MAGIC %md ## Validate — counts + hero

# COMMAND ----------
for t in ["clients","instruments","positions","research_notes","filing_facts","news_events_tagged"]:
    print(f"{PFX}_silver.{t}:", spark.table(f"{SILVER}.{t}").count())
wti = spark.sql(f"SELECT sum(net_qty) q FROM {SILVER}.positions p JOIN {SILVER}.clients c ON p.client_id=c.client_id WHERE c.ticker='AC.TO' AND p.instrument_id='WTI'").collect()[0].q
assert wti and wti > 0, "HERO BROKEN: AC should be net-long WTI"
print("HERO OK — AC net-long WTI:", wti)

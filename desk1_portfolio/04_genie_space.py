#!/usr/bin/env python3
"""
Desk 1 · D1.4 — Portfolio & Exposure Genie space (Path B / code).

Builds the serialized_space via the genie-rooms GenieSpaceBuilder (handles version=2,
sorted data_sources, id-keyed lists) and writes the create payload. Create with:

  databricks api post /api/2.0/genie/spaces --profile pbb-demo --json @/tmp/create_portfolio_space.json

The description + instructions are authored deliberately — they are the top routing signal
for Genie One discovery / OntoRank (see PLAN.md 2a). Genie Code prompt equivalent: RUNBOOK D1.4.
"""
import json, sys

SKILL = "/Users/elmer.cecilio/.vibe/marketplace/plugins/fe-internal-tools/skills/genie-rooms/resources"
sys.path.insert(0, SKILL)
from genie_space_builder import GenieSpaceBuilder  # noqa: E402

import argparse
_p = argparse.ArgumentParser()
_p.add_argument("--catalog", default="ec_demo_workspace")
_p.add_argument("--warehouse-id", required=True, help="a serverless SQL warehouse id in YOUR workspace")
_a = _p.parse_args()
CATALOG = _a.catalog
WAREHOUSE = _a.warehouse_id

space = GenieSpaceBuilder(
    title="Portfolio & Exposure — CM Desk",
    description=(
        "Structured analytics for the Portfolio & Exposure trading desk. Answers questions about "
        "client positions, gross notional and net exposure by sector / desk / currency / asset class, "
        "unrealized PnL, and price-shock PnL impact. Use this space for 'exposure', 'notional', "
        "'PnL', 'which clients hold instrument X', and desk/sector risk roll-ups."
    ),
    warehouse_id=WAREHOUSE,
)
space.set_instructions(
    f"Prefer the metric view {CATALOG}.cm_portfolio_metrics.exposure_kpis for any aggregate "
    "(gross notional, net exposure, unrealized PnL, counts) via MEASURE(); GROUP BY the named "
    "dimensions (Client, Ticker, Sector, Desk, Book, Currency, Asset Class, Coverage Officer). "
    "Use the positions view for row-level detail. Amounts are CAD. State the grain and any filters "
    "in the answer."
)
space.add_metric_view(f"{CATALOG}.cm_portfolio_metrics.exposure_kpis")
space.add_view(f"{CATALOG}.cm_portfolio_gold.positions")
space.add_view(f"{CATALOG}.cm_portfolio_gold.clients")
space.add_example_sql(
    title="Gross notional by sector",
    sql=(
        "SELECT `Sector`, MEASURE(`Gross Notional CAD`) AS gross_notional_cad\n"
        f"FROM {CATALOG}.cm_portfolio_metrics.exposure_kpis\n"
        "GROUP BY `Sector` ORDER BY gross_notional_cad DESC"
    ),
)
space.add_example_sql(
    title="Air Canada oil exposure",
    sql=(
        "SELECT instrument_id, net_qty, gross_notional_cad\n"
        f"FROM {CATALOG}.cm_portfolio_gold.positions\n"
        "WHERE ticker = 'AC.TO' AND asset_class = 'commodity' ORDER BY gross_notional_cad DESC"
    ),
)
space.validate()

payload = {
    "title": space.title,
    "description": space.description,
    "warehouse_id": space.warehouse_id,
    "serialized_space": json.dumps(space.to_dict()),
}
out = "/tmp/create_portfolio_space.json"
with open(out, "w") as f:
    json.dump(payload, f, indent=2)
print("wrote", out)

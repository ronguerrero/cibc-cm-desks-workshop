#!/usr/bin/env python3
"""Desk 3 · D3.2 — Market Intelligence Genie space (Path B). Create with:
   databricks api post /api/2.0/genie/spaces --profile pbb-demo --json @/tmp/create_market_space.json
"""
import json, sys
sys.path.insert(0, "/Users/elmer.cecilio/.vibe/marketplace/plugins/fe-internal-tools/skills/genie-rooms/resources")
from genie_space_builder import GenieSpaceBuilder  # noqa: E402

import argparse
_p = argparse.ArgumentParser()
_p.add_argument("--catalog", default="ec_demo_workspace")
_p.add_argument("--warehouse-id", required=True, help="a serverless SQL warehouse id in YOUR workspace")
_a = _p.parse_args()
CATALOG, WAREHOUSE = _a.catalog, _a.warehouse_id
space = GenieSpaceBuilder(
    title="Market Intelligence — CM Desk",
    description=(
        "Market-news and signal analytics for the Market Intelligence desk. Answers questions about "
        "tagged news events, sentiment / adverse media, and which clients are exposed to a market "
        "event (via signal matches). Use for 'adverse media on X', 'which clients are exposed to the "
        "OPEC/oil news', news sentiment, and event-to-portfolio signal questions."
    ),
    warehouse_id=WAREHOUSE,
)
space.set_instructions(
    "Use signal_matches to answer which clients are exposed to a news event (join is pre-built: "
    "client, ticker, matched asset class, position, PnL, headline, sentiment). Use news_events for "
    "headlines, sentiment_label, entities, and themes (e.g. adverse media = sentiment_label='bearish'). "
    "Arrays entities/asset_classes/themes: filter with array_contains(). Amounts CAD."
)
space.add_view(f"{CATALOG}.cm_market_gold.signal_matches")
space.add_view(f"{CATALOG}.cm_market_gold.news_events")
space.add_example_sql(
    title="Clients exposed to oil (WTI) news",
    sql=("SELECT client_name, ticker, sentiment_label, headline\n"
         f"FROM {CATALOG}.cm_market_gold.signal_matches\n"
         "WHERE matched_asset_class = 'WTI' ORDER BY client_name"),
)
space.add_example_sql(
    title="Adverse (bearish) market news",
    sql=("SELECT published_at, source, headline\n"
         f"FROM {CATALOG}.cm_market_gold.news_events\n"
         "WHERE sentiment_label = 'bearish' ORDER BY published_at DESC"),
)
space.validate()
payload = {"title": space.title, "description": space.description,
           "warehouse_id": space.warehouse_id, "serialized_space": json.dumps(space.to_dict())}
open("/tmp/create_market_space.json", "w").write(json.dumps(payload, indent=2))
print("wrote /tmp/create_market_space.json")

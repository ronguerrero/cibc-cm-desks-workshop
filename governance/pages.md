# Discover Pages — CM desks (concept / ontology layer)

Pages are the human-modeled ontology on top of the domains: business terms with synonyms, a
definition, business-use guidance, and related assets. They feed the **Genie Ontology** that Genie
One's OntoRank uses, so they sharpen discovery ("adverse media", "the wall") → the right desk.

**Pages have NO public API** (REST/CLI/SDK all 404; the Beta bulk-create path fails with "Create API
returned no page" — not permissions, not content). **Author them by hand in the Discover editor.**
This file is the source of truth so they can be created (or recreated) consistently.

## How to create one (UI recipe + gotchas)
Discover → open the desk's **domain** → **Create ▸ Create page** (only enabled inside a domain), or
`/discover/pages/new?domainId=<domain_id>`. Then:
1. Type the page name.
2. Body is pre-templated with **Definition** and **Business use** H3s — click the paragraph under each and type.
3. **Synonyms:** Add synonym → type → Enter (the input closes each time; click Add synonym again for the next).
4. **Related Assets:** Add related asset → search → pick. Tables / metric views / views are searchable;
   **UC functions are NOT** in the picker — name them in prose instead.
5. **Description is REQUIRED** — Publish stays disabled until it's filled.
6. **Publish.** (Author with real keystrokes — browser automation of these widgets is flaky.)

Domain ids: Portfolio `65bd9c6a-7b16-4cbf-af83-3f9b2da45df5` · Research `a45eaf62-8138-4e58-a387-3cc92d4334c9` · Market `d5ef1458-c4f0-4dac-8de8-3118ab95fbb2`.

---

## Page 1 — Gross Notional CAD  *(domain: CM Portfolio and Exposure)*
- **Synonyms:** notional, gross exposure, gross notional, book size
- **Description:** The total gross CAD value of a book's positions — the governed `Gross Notional CAD` measure in `cm_portfolio_metrics.exposure_kpis`.
- **Definition:** Gross Notional CAD is the sum of the absolute CAD-converted notional of every position, ignoring long/short sign. The single governed source of truth is the `Gross Notional CAD` measure in the `exposure_kpis` metric view — defined once and reused by the Genie space, the desk agent, and any dashboard so the number never drifts.
- **Business use:** Size a desk, sector, or client's footprint. When a user asks about "notional", "book size", or "how big is our exposure", resolve it to this measure rather than summing raw position rows. For directional risk, use Net Exposure CAD instead.
- **Related assets:** `cm_portfolio_metrics.exposure_kpis`, `cm_portfolio_gold.positions`

## Page 2 — Net Exposure CAD  *(domain: CM Portfolio and Exposure)*
- **Synonyms:** net exposure, directional exposure, net position value
- **Description:** Signed CAD exposure (longs minus shorts) — the governed `Net Exposure CAD` measure in `exposure_kpis`.
- **Definition:** Net Exposure CAD sums CAD notional with sign (long positive, short negative), so it reflects directional risk that Gross Notional hides. It is the `Net Exposure CAD` measure in the `exposure_kpis` metric view.
- **Business use:** Judge which way a book leans and what a price move does to it. Pair with `compute_shock_pnl` to estimate the PnL impact of a shock (e.g. Air Canada is net-long oil, so a WTI drop is a loss).
- **Related assets:** `cm_portfolio_metrics.exposure_kpis`, `cm_portfolio_gold.positions`

## Page 3 — Coverage Officer & the Chinese Wall  *(domain: CM Portfolio and Exposure)*
- **Synonyms:** coverage, chinese wall, information barrier, coverage officer, need-to-know
- **Description:** The information barrier that limits each user to the clients they cover — enforced by row filters on the desk data products.
- **Definition:** Every client has a coverage officer. The `cm_governance.coverage_wall` / `coverage_wall_client` row-filter functions (driven by the `coverage_acl` map) restrict rows so a user sees only clients mapped to them, unless they are in the `cm_all_access` group. The filter follows the data through Genie, the UC functions, and the desk/firm agents.
- **Business use:** The governed answer to "who is allowed to see this book?" — a coverage officer sees only their names; the same question from two people returns different, compliant results. Applied to clients, positions, research_docs, and signal_matches.
- **Related assets:** `cm_portfolio_gold.clients`, `cm_portfolio_gold.positions`

## Page 4 — House View  *(domain: CM Research and Filings)*
- **Synonyms:** analyst view, research view, desk view, recommendation, coverage note
- **Description:** The desk's published research opinion on a client — retrieved from the analyst research corpus via the Research Knowledge Assistant.
- **Definition:** The House View is the analyst desk's current opinion (thesis, hedging stance, risks, recommendation) on a covered name. It lives in the `cm_research_gold.research_docs` corpus and is served through the Research Knowledge Assistant, which returns grounded, cited answers. For exact disclosed numbers (e.g. hedge-policy limits), use `get_filing_facts` rather than the narrative.
- **Business use:** Answer "what do we think about X?" or "what's our view on X's hedging?". Distinguish the qualitative house view (KA) from the hard filing facts (function) — the Research Desk Agent composes both.
- **Related assets:** `cm_research_gold.research_docs`

## Page 5 — Adverse Media  *(domain: CM Market Intelligence)*
- **Synonyms:** negative news, adverse news, bearish coverage, negative sentiment, red flags
- **Description:** Negative-sentiment market news relevant to a client — the bearish slice of the tagged news events, joined to client exposure.
- **Definition:** Adverse Media is market news tagged with negative (bearish) sentiment. In `cm_market_gold.news_events` it is `sentiment_label = 'bearish'`; `signal_matches` links each event to the clients exposed to it (by asset class), with the affected position and PnL. Served through the Market Intelligence Genie space and `get_client_signals`.
- **Business use:** Answer "any adverse media on X?" or "which clients are hit by the OPEC/oil news?". Screen coverage names for negative signals and tie a headline to who in the book it moves.
- **Related assets:** `cm_market_gold.news_events`, `cm_market_gold.signal_matches`

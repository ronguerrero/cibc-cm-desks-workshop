# R3 — "I have tables. How do I make a Genie agent over them?"

Proven in `desk1_portfolio/` (01→02→04).

1. **Gold view + certify** — a clean, business-named view; certify for trust/discovery:
```sql
CREATE OR REPLACE VIEW <cat>.<schema>.my_gold AS SELECT ... FROM <source>;
ALTER VIEW <cat>.<schema>.my_gold SET TAGS ('system.certification_status' = 'certified');
```
2. **Metric view (semantic layer)** — named measures + dimensions with descriptions (this is the
   top OntoRank/discovery signal and lets Genie answer with governed numbers):
```sql
CREATE OR REPLACE VIEW <cat>.<schema>.my_kpis WITH METRICS LANGUAGE YAML AS $$
version: 0.1
source: <cat>.<schema>.my_gold
dimensions: [{name: Sector, expr: sector}, ...]
measures:   [{name: Gross Notional CAD, expr: SUM(gross_notional_cad)}, ...]
$$;
ALTER VIEW <cat>.<schema>.my_kpis SET TAGS ('system.certification_status'='certified');
```
   Query with `MEASURE()`: `SELECT Sector, MEASURE(\`Gross Notional CAD\`) ... GROUP BY Sector`.
3. **Genie space** — author description + instructions + sample questions deliberately (the biggest
   routing lever). Build via the `GenieSpaceBuilder` helper then `POST /api/2.0/genie/spaces`
   (see `desk1_portfolio/04_genie_space.py`), or via Genie Code prompt.

## ✓ Validation
Ask the space a question → it should generate `MEASURE()` SQL over the metric view. In this build
"gross notional by sector" → Energy $2.78B, tying the raw aggregate to the penny.

## Tips
- Metric-view `MEASURE()` totals must tie to the raw aggregate — check before publishing.
- Genie `serialized_space` is iteration-heavy: version 2, `data_sources.tables` sorted by
  identifier, id-keyed lists sorted by id, one text-instruction item. The helper handles this.

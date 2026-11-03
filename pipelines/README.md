# Pipelines

Scheduled ETL jobs. Pipelines are the only code that writes data tables; API request
handlers only read. Each run records a row in `etl_runs` and every ingested file becomes a
new `datasets` row (with checksum), so nothing is overwritten silently.

| Pipeline | Writes | Step |
|---|---|---|
| `ingest_businesses` | `datasets`, `businesses` (SEMAS store info) | 4 |
| `ingest_trade_areas` | `datasets`, `trade_areas` (Seoul trade-area polygons) | 5 |
| `ingest_metrics` | `datasets`, `trade_area_metrics` (population, sales, store counts) | 5 |
| `ingest_pois` | `datasets`, `pois` (stations, stops, schools, offices) | 5 |
| `build_grid` | `grid_cells` (national-grid-aligned 250 m / 100 m cells) | 6 |
| `compute_scores` | `score_baselines`, `grid_scores` | 6 |
| `seed_demo` | synthetic, `is_synthetic = true` data for demo mode | 3 |

Raw downloads go to `data/raw/` (git-ignored). Source licences and access methods: `docs/datasets.md`.

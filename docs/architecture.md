# Architecture

## Overview

```
 Browser (Next.js on Vercel/Firebase)
   │  Kakao Maps JS SDK (domain-restricted JS key only)
   │  HTTPS JSON
   ▼
 FastAPI (container: Cloud Run or similar)  ── reads only ──►  PostgreSQL + PostGIS
   │  /api/locations/search → Kakao Local API (server key, not persisted)        ▲
                                                                                  │ writes
 Scheduled pipelines (pandas / GeoPandas)  ── ingest · clean · precompute ────────┘
   ◄── data.go.kr (SEMAS), Seoul Open Data Plaza, golmok.seoul.go.kr
```

Principles:

1. **Request handlers never compute heatmaps or fetch public data.** Pipelines precompute;
   handlers read. A point analysis (`/analyze`) does run a few indexed PostGIS queries
   (`ST_DWithin` on EPSG:5179 points, point-in-trade-area), which are bounded by the radius limit.
2. **Provenance everywhere.** Every data row references `datasets.id`. Every analysis response
   returns `sources` (dataset, resolution, period, licence status) and `confidence`.
3. **Metric storage, WGS84 I/O.** All geometry is EPSG:5179 (metres) with a GIST index.
   The API converts to WGS84 at the boundary.
4. **Expansion by data and configuration.** A new district = more rows; a new category =
   a `categories` row + `category_map` rows + a `score_configs` row. No code restructuring.
5. **Synthetic data is labelled at the source** (`datasets.is_synthetic`) and propagated as
   `is_sample` in every response; the UI shows a persistent "샘플 데이터" badge.

## Repository layout

```
gilmok/
  apps/web/            Next.js (App Router), Tailwind, shadcn/ui, Kakao Maps, Recharts
    app/  components/{map,panels,charts,ui}  lib/api/{client.ts,schema.ts (generated)}
  services/api/        FastAPI
    app/core/          config, db, geo (CRS + distance), params (validation), errors
    app/models/        SQLAlchemy + GeoAlchemy2 tables
    app/schemas/       Pydantic API contract
    app/routers/       HTTP endpoints
    app/services/      domain logic: competition, demand, scoring, recommendations, explanation
    migrations/        Alembic
    tests/
  pipelines/           ETL jobs (see pipelines/README.md)
  data/raw/            git-ignored downloads;   data/demo/  labelled synthetic data
  docs/                architecture.md, datasets.md, scoring.md
```

## Database

| Table | Purpose | Key spatial / index |
|---|---|---|
| `datasets` | One row per ingested dataset version; provenance, resolution, period, licence status, `is_synthetic` | — |
| `etl_runs` | Pipeline run history | — |
| `categories` | Internal categories (`cafe`, …) and whether enabled | — |
| `category_map` | (`source_system`, `source_code`) → `category_key` | — |
| `businesses` | SEMAS stores | `geom` POINT 5179, GIST; (`category_key`, `dataset_id`) |
| `trade_areas` | Seoul 상권 polygons | `geom` MULTIPOLYGON 5179, GIST |
| `trade_area_metrics` | Long format: (`trade_area_id`, `metric_key`, `category_key`, `period`, `value`) | unique natural key (NULLS NOT DISTINCT) |
| `pois` | Stations, stops, schools, universities, offices, attractions | `geom` POINT 5179, GIST; `kind` |
| `grid_cells` | Analysis cells aligned to the national grid; containing trade area | `geom` POLYGON 5179, GIST |
| `score_configs` | Weights + component definitions per category, versioned | — |
| `score_baselines` | Seoul-wide sorted values per metric for percentile normalisation | — |
| `grid_scores` | Precomputed components, total, coverage, missing reasons, data versions | (`config_id`, `data_version`) |
| `saved_locations` | Anonymous-session candidates with frozen analysis snapshot | `geom` POINT 5179, GIST |
| `response_cache` | Analysis cache keyed by (rounded point, radius, category, weights, data version) | — |

Refinements over the original brief: `categories` and `category_map.source_system` (SEMAS and
golmok use different code systems), `etl_runs`, `score_baselines`, `grid_scores.status/missing`,
`datasets.is_synthetic/license_status`, `response_cache`.

## API

All endpoints return errors as `{code, message, details}` (`code` English, `message` Korean).

| Method & path | Notes | Step |
|---|---|---|
| `GET /api/health` | | 1 ✅ |
| `GET /api/datasets/status` | Latest version of each dataset + last ETL run | 1 ✅ |
| `GET /api/locations/search?q=` | Kakao Local proxy; never persisted | 3 |
| `GET /api/businesses/nearby?lat&lng&radius&category&page&page_size` | Stores + competition metrics | 4 |
| `GET /api/locations/analyze?lat&lng&radius&category&weights` | Components, total, coverage, evidence, risks | 5 |
| `GET /api/heatmap?bbox&category&cell_size&weights` | Precomputed GeoJSON; gray cells carry a reason | 6 |
| `GET /api/locations/recommendations?bbox\|district&category&weights&limit` | Top-N cells | 6 |
| `GET/POST /api/saved-locations`, `DELETE /api/saved-locations/{id}` | Header `X-Owner-Key` | 6 |
| `GET /api/locations/compare?ids=` | 2–3 saved ids; tradeoffs, no winner | 6 |

Parameter rules: `radius ∈ {300, 500, 1000}`; `cell_size ∈ {100, 250}`; `bbox =
minLng,minLat,maxLng,maxLat` with max area `MAX_BBOX_AREA_KM2` (default 100 km²);
`weights = demand:0.35,competition:0.25,…` (omitted keys keep defaults, result normalised to sum 1).
Pagination returns `{page, page_size, total}`.

Weights and the heatmap: precomputed `grid_scores` store **component** scores, so a custom-weight
heatmap is a cheap weighted average over stored components at read time, not a recomputation.

## Explanations (no LLM in the MVP)

The AI consultant is deferred for cost reasons. Explanations are rule-based Korean sentences
generated only from fields already in the response. The service interface leaves room for an
LLM later, with the same rule: it may only restate numbers present in the input JSON.

## Deployment (decided in Step 7)

Candidate: Next.js on Firebase App Hosting (or Vercel), API container on Cloud Run, PostGIS on a
managed host (Supabase / Neon free tier, or Cloud SQL — paid). `services/api/Dockerfile` is
host-agnostic.

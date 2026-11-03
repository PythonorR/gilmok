# Scoring (draft — finalised in Step 5, tests first)

**The score is a relative composite of input indicators. It is not a probability of business
success and must never be labelled as one.**

## Components (0–100, higher = more favourable)

| Component | Inputs | Resolution | Initial weight |
|---|---|---|---|
| Demand | trade-area residential, working, floating, street-level population; nearby offices, schools, universities, attractions. **Not** estimated sales. | trade area + point | 0.35 |
| Competition | estimated demand per same-category store = trade-area estimated sales ÷ same-category store count. Raw store count is **not** penalised. | trade area | 0.25 |
| Accessibility | distance to nearest station/stop; number of stops within radius | point | 0.20 |
| Growth | trade-area change indicators; store-count change | trade area | 0.10 |
| Cost | regional rent indicators — MVP default: **missing** | — | 0.10 |

Weights are assumptions, not validated; they are user-adjustable and stored per category in
`score_configs`. No variable appears in both Demand and Competition (sales is only in Competition).

Explanatory-only metrics (shown, never scored): competitor count, density, nearest-competitor
distance, mean nearest-neighbour distance, Clark–Evans clustering ratio.

## Normalisation

Each component is converted to a percentile (0–100) against the distribution of **all Seoul
trade areas**, stored in `score_baselines` per data version. Lower-is-better metrics (e.g.
distance to station) are reversed. Consequence: v1 must ingest Seoul-wide trade-area metrics
even though map coverage is Mapo-gu only.

## Missing data and coverage

$$S = \frac{\sum_{k \in A} w_k S_k}{\sum_{k \in A} w_k}, \qquad \text{coverage} = \sum_{k \in A} w_k$$

with weights normalised to sum to 1 and A = components with data. Missing components are never
imputed as perfect or average; they are listed explicitly (e.g. "임대료 제외"). If
`coverage < 0.70` (assumption, per `score_configs.min_coverage`), the result is
`insufficient_data`: no total is shown, and the map cell is gray with a reason.

With cost missing in the MVP, maximum coverage is 0.90.

## Known structural limitations

- **Cells inside one trade area share Demand (population part), Competition and Growth.**
  Differences between such cells come only from point data: Accessibility and POI-based Demand.
- **Points outside every trade-area polygon** have no trade-area metrics. Demand (partly),
  Competition and Growth are missing, coverage falls below 0.70 → "상권 경계 밖 — 데이터 부족".
- Scores are comparable only under the same config version, data versions and coverage;
  `grid_scores.data_version` records this.

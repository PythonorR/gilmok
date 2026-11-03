"""Pydantic request/response schemas — the public API contract.

Conventions: coordinates are WGS84 (lat/lng); distances in metres; money in KRW;
scores are 0–100 where higher is more favourable. Every analysis payload carries
`confidence` and `sources`, and `is_sample` is true whenever synthetic data was used.
"""

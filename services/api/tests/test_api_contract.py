"""HTTP-level contract: one error format everywhere, validation before stubs."""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
OWNER = {"X-Owner-Key": "a1b2c3d4-e5f6-4711-8899-aabbccddeeff"}


def _assert_error(resp, status, code):
    assert resp.status_code == status
    body = resp.json()
    assert set(body) == {"code", "message", "details"}
    assert body["code"] == code


def test_health():
    assert client.get("/api/health").json()["status"] == "ok"


def test_invalid_radius_uses_error_format():
    r = client.get("/api/locations/analyze", params={"lat": 37.556, "lng": 126.923, "radius": 750})
    _assert_error(r, 400, "INVALID_RADIUS")


def test_missing_param_uses_error_format():
    _assert_error(
        client.get("/api/locations/analyze", params={"lat": 37.5}), 422, "VALIDATION_ERROR"
    )


def test_unknown_route_uses_error_format():
    _assert_error(client.get("/api/nope"), 404, "NOT_FOUND")


@pytest.mark.parametrize(
    ("path", "params"),
    [
        ("/api/locations/analyze", {"lat": 37.556, "lng": 126.923, "radius": 500}),
        ("/api/businesses/nearby", {"lat": 37.556, "lng": 126.923}),
        ("/api/heatmap", {"bbox": "126.88,37.53,126.97,37.59"}),
        ("/api/locations/recommendations", {"district": "11440"}),
    ],
)
def test_valid_requests_reach_stub(path, params):
    _assert_error(client.get(path, params=params), 501, "NOT_IMPLEMENTED")


def test_recommendations_requires_exactly_one_area():
    _assert_error(client.get("/api/locations/recommendations"), 400, "INVALID_AREA")


def test_compare_validates_ids():
    _assert_error(
        client.get("/api/locations/compare", params={"ids": "x,y"}, headers=OWNER),
        400,
        "INVALID_IDS",
    )


def test_owner_key_required():
    _assert_error(client.get("/api/saved-locations"), 422, "VALIDATION_ERROR")


def test_openapi_has_no_secrets():
    text = client.get("/openapi.json").text.lower()
    for word in ("service_key", "api_key", "secret"):
        assert word not in text

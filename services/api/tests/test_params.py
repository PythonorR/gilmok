import pytest

from app.core.errors import AppError
from app.core.params import (
    parse_bbox,
    parse_weights,
    validate_category,
    validate_cell_size,
    validate_point,
    validate_radius,
)
from app.routers.deps import DEFAULT_WEIGHTS

MAPO_BBOX = "126.88,37.53,126.97,37.59"  # roughly Mapo-gu


def _code(fn, *args):
    with pytest.raises(AppError) as exc:
        fn(*args)
    return exc.value.code


@pytest.mark.parametrize("r", [300, 500, 1000])
def test_allowed_radii(r):
    assert validate_radius(r) == r


@pytest.mark.parametrize("r", [0, 250, 750, 2000, -500])
def test_rejected_radii(r):
    assert _code(validate_radius, r) == "INVALID_RADIUS"


def test_cell_sizes():
    assert validate_cell_size(250) == 250
    assert validate_cell_size(100) == 100
    assert _code(validate_cell_size, 50) == "INVALID_CELL_SIZE"


def test_point_bounds():
    validate_point(37.556, 126.923)
    assert _code(validate_point, 126.923, 37.556) == "OUT_OF_BOUNDS"  # swapped lat/lng
    assert _code(validate_point, 35.68, 139.76) == "OUT_OF_BOUNDS"  # Tokyo


def test_category():
    assert validate_category("cafe", ("cafe",)) == "cafe"
    assert _code(validate_category, "restaurant", ("cafe",)) == "UNSUPPORTED_CATEGORY"


def test_bbox_ok_and_area():
    bbox = parse_bbox(MAPO_BBOX, 100)
    assert 30 < bbox.area_km2 < 60


@pytest.mark.parametrize("raw", ["", "1,2,3", "a,b,c,d", "126.97,37.53,126.88,37.59"])
def test_bbox_invalid(raw):
    assert _code(parse_bbox, raw, 100) == "INVALID_BBOX"


def test_bbox_too_large():
    assert _code(parse_bbox, "126.7,37.4,127.2,37.7", 100) == "BBOX_TOO_LARGE"


def test_weights_default_sum_to_one():
    w = parse_weights(None, DEFAULT_WEIGHTS)
    assert sum(w.values()) == pytest.approx(1.0)
    assert w["demand"] == pytest.approx(0.35)


def test_weights_partial_override_is_renormalised():
    w = parse_weights("cost:0", DEFAULT_WEIGHTS)
    assert w["cost"] == 0
    assert sum(w.values()) == pytest.approx(1.0)
    assert w["demand"] == pytest.approx(0.35 / 0.9)


@pytest.mark.parametrize(
    "raw", ["demand", "foo:0.5", "demand:x", "demand:-1", "demand:nan", "demand:inf"]
)
def test_weights_invalid(raw):
    assert _code(parse_weights, raw, DEFAULT_WEIGHTS) == "INVALID_WEIGHTS"


def test_weights_all_zero_rejected():
    raw = "demand:0,competition:0,accessibility:0,growth:0,cost:0"
    assert _code(parse_weights, raw, DEFAULT_WEIGHTS) == "INVALID_WEIGHTS"

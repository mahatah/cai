"""run_to_jsonl must record a float cost from whatever a provider put on the response."""

import pytest

from cai.sdk.agents.run_to_jsonl import _coerce_cost


@pytest.mark.parametrize(
    "value,expected",
    [
        (None, 0.0),
        (0.00067, 0.00067),
        (3, 3.0),
        ("0.5", 0.5),
        ({"usd": 0.00067, "diem": 0.0}, 0.00067),  # Venice.ai response shape
        ({"total": 0.2}, 0.2),
        ({"cost": 0.1}, 0.1),
        ({"diem": 0.1}, 0.0),
        ({"usd": "n/a"}, 0.0),
        ("garbage", 0.0),
        (True, 0.0),
        ([1, 2], 0.0),
    ],
)
def test_coerce_cost_never_raises(value, expected):
    assert _coerce_cost(value) == pytest.approx(expected)

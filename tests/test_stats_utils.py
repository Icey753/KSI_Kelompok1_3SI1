import pytest

from src.stats_utils import ci95_halfwidth, mann_whitney_p


def test_ci95_constant_samples_is_zero():
    assert ci95_halfwidth([2.0, 2.0, 2.0]) == 0.0


def test_ci95_single_sample_is_zero():
    assert ci95_halfwidth([5.0]) == 0.0


def test_ci95_known_value():
    # std(ddof=1)=1.5811, n=5 -> 1.96 * 1.5811 / sqrt(5) = 1.3859
    assert ci95_halfwidth([1, 2, 3, 4, 5]) == pytest.approx(1.3859, abs=1e-3)


def test_mann_whitney_identical_samples_high_p():
    data = list(range(50))
    assert mann_whitney_p(data, data) > 0.9


def test_mann_whitney_separated_samples_low_p():
    a = list(range(50))
    b = [x + 1000 for x in range(50)]
    assert mann_whitney_p(a, b) < 1e-6

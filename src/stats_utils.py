import math
from collections.abc import Sequence

import numpy as np
from scipy.stats import mannwhitneyu


def ci95_halfwidth(samples: Sequence[float]) -> float:
    """Half-width of the 95% normal-approximation CI of the MEAN (not the median); assumes n >= 30."""
    n = len(samples)
    if n < 2:
        return 0.0
    return float(1.96 * np.std(samples, ddof=1) / math.sqrt(n))


def mann_whitney_p(a: Sequence[float], b: Sequence[float]) -> float:
    return float(mannwhitneyu(a, b, alternative="two-sided").pvalue)

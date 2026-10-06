"""Reproducible research sampling, binary metrics and paired match bootstrap."""

from numbers import Integral

import numpy as np
import pandas as pd

from tabpfn_xg.calibration import probability_check


def _labels(y):
    y = np.asarray(y)
    if y.ndim != 1 or not len(y) or not np.isin(y, [0, 1]).all():
        raise ValueError("Labels must be a nonempty one-dimensional binary vector")
    return y.astype(float)


def _integer(value, name, minimum):
    if isinstance(value, bool) or not isinstance(value, Integral) or value < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}")


def sample_rows(rows, y, seed, size):
    """Sample positional rows with nested class permutations and rounded prevalence.

    Same seed and pool give nested membership across sizes, not prefix ordering.
    Pass only historical fit-role positions; this function does not assign splits.
    """
    y = _labels(y)
    rows = np.asarray(rows)
    if (rows.ndim != 1 or not len(rows) or rows.dtype.kind not in "iu"
            or (rows < 0).any() or (rows >= len(y)).any()
            or len(np.unique(rows)) != len(rows)):
        raise ValueError("Rows must be unique, nonempty integer positions within labels")
    _integer(seed, "Seed", 0)
    _integer(size, "Sample size", 0)
    if size > len(rows):
        raise ValueError("Sample size exceeds the available row pool")
    rng = np.random.default_rng(seed)
    by_class = [rng.permutation(rows[y[rows] == c]) for c in (0, 1)]
    goals = round(size * np.mean(y[rows]))
    result = np.concatenate([by_class[0][:size - goals], by_class[1][:goals]])
    return rng.permutation(result)


def metrics(y, p):
    """Return research scores; AUC is NaN for a single-class sample.

    Log loss clips float64 probabilities at machine epsilon, as in the source
    sklearn metric. Brier and ranking use the original validated probabilities.
    """
    y = _labels(y)
    p = probability_check(p, len(y))
    clipped = np.clip(p, np.finfo(float).eps, 1 - np.finfo(float).eps)
    positives = int(y.sum())
    negatives = len(y) - positives
    auc = float("nan")
    if positives and negatives:
        ranks = pd.Series(p).rank(method="average").to_numpy()
        auc = float((ranks[y == 1].sum() - positives * (positives + 1) / 2)
                    / (positives * negatives))
    return dict(log_loss=float(np.mean(-(y * np.log(clipped)
                                         + (1 - y) * np.log1p(-clipped)))),
                brier=float(np.mean((p - y) ** 2)), auc=auc,
                predicted_rate=float(p.mean()), observed_rate=float(y.mean()),
                shots=len(y), goals=positives)


def clustered_difference(y, a, b, groups, *, seed=123, replicates=2000):
    """Return a-minus-b loss differences and percentile 95% match intervals.

    Sample whole matches with replacement, keeping all their shots and pairing
    the two models. Repeated matches contribute repeatedly; losses remain shot
    weighted. Defaults reproduce the frozen protocol. As in research, clipping
    at 1e-15 also carries into the bootstrap's Brier calculation.
    """
    y = _labels(y)
    a = probability_check(a, len(y))
    b = probability_check(b, len(y))
    groups = np.asarray(groups)
    if groups.shape != y.shape or pd.isna(groups).any():
        raise ValueError("Match groups must align with labels and contain no missing IDs")
    if groups.dtype.kind in "fc" and not np.isfinite(groups).all():
        raise ValueError("Match groups must contain finite IDs")
    try:
        group_ids, inverse = np.unique(groups, return_inverse=True)
    except TypeError as error:
        raise ValueError("Match IDs must have mutually sortable types") from error
    _integer(seed, "Seed", 0)
    _integer(replicates, "Bootstrap replicates", 1)
    counts = np.bincount(inverse)
    rng = np.random.default_rng(seed)
    draws = rng.integers(0, len(group_ids), size=(replicates, len(group_ids)))
    a, b = [np.clip(p, 1e-15, 1 - 1e-15) for p in (a, b)]
    deltas = {
        "log_loss": -(y * np.log(a) + (1 - y) * np.log1p(-a))
                    + (y * np.log(b) + (1 - y) * np.log1p(-b)),
        "brier": (a - y) ** 2 - (b - y) ** 2,
    }
    result = {}
    for name, delta in deltas.items():
        totals = np.bincount(inverse, weights=delta)
        distribution = totals[draws].sum(1) / counts[draws].sum(1)
        result[name] = dict(difference=float(delta.mean()),
                            ci95=np.quantile(distribution, [.025, .975]).tolist())
    return result

"""Binary probability boundaries and application of frozen logit calibration."""

from dataclasses import dataclass
from numbers import Integral

import numpy as np


def _numeric_array(value, name):
    try:
        if np.iscomplexobj(value):
            raise ValueError("Complex values are not real probabilities or parameters")
        return np.asarray(value, dtype=float)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError(f"{name} must contain numeric values") from error


def probability_check(p, n):
    """Return a finite probability vector of exactly n rows, including endpoints."""
    if isinstance(n, bool) or not isinstance(n, Integral) or n < 0:
        raise ValueError("Expected row count must be a nonnegative integer")
    p = _numeric_array(p, "Probabilities")
    if p.shape != (n,):
        raise ValueError(f"Expected probability shape {(n,)}, got {p.shape}")
    if not np.isfinite(p).all() or (p < 0).any() or (p > 1).any():
        raise ValueError("Probabilities must be finite and between 0 and 1")
    return p


def positive_probability(model, x):
    """Call predict_proba and map the goal class (1) through model.classes_."""
    p = _numeric_array(model.predict_proba(x), "Class probabilities")
    classes = np.asarray(model.classes_)
    if classes.shape != (2,) or not (
        np.array_equal(classes, [0, 1]) or np.array_equal(classes, [1, 0])
    ):
        raise ValueError("Expected exactly two binary classes labelled 0 and 1")
    if p.shape != (len(x), 2):
        raise ValueError(f"Expected class probability shape {(len(x), 2)}, got {p.shape}")
    probability_check(p.reshape(-1), len(x) * 2)
    # Preserve the source's np.allclose row-sum tolerance (rtol=1e-5, atol=1e-8).
    if not np.allclose(p.sum(axis=1), 1, rtol=1e-5, atol=1e-8):
        raise ValueError("Binary class probability rows must sum to 1")
    return probability_check(p[:, int(np.flatnonzero(classes == 1)[0])], len(x))


@dataclass(frozen=True)
class Calibration:
    """Explicit sigmoid(a * logit(clipped p) + b) parameters; no fitting."""

    a: float
    b: float
    clip: float = 1e-7

    def __post_init__(self):
        values = _numeric_array([self.a, self.b, self.clip], "Calibration parameters")
        if (values.shape != (3,) or not np.isfinite(values).all()
                or values[0] <= 0 or not 0 < values[2] < 0.5):
            raise ValueError("Calibration requires finite a > 0, finite b and 0 < clip < 0.5")
        for name, value in zip(("a", "b", "clip"), values):
            object.__setattr__(self, name, float(value))


# provenance/research_manifest.json: external_experiment.frozen_selection.
# Selected on historical matches, before the external evaluation.
CATBOOST_CALIBRATION = Calibration(1.0123564537857361, 0.08384092826439743)
TABPFN_CALIBRATION = Calibration(1.023112240680613, 0.070507598294854)


def apply_calibration(p, calibration):
    """Validate raw probabilities, clip endpoints and apply supplied parameters.

    Use the frozen model constants for reproduction. Cached evaluation CSV values
    are already calibrated and must not pass through this function again.
    """
    if not isinstance(calibration, Calibration):
        raise ValueError("Supply an explicit Calibration instance")
    p = _numeric_array(p, "Probabilities")
    if p.ndim != 1:
        raise ValueError("Expected a one-dimensional probability vector")
    p = probability_check(p, len(p))
    clipped = np.clip(p, calibration.clip, 1 - calibration.clip)
    # Match scipy.special.logit arithmetic used by the research implementation.
    with np.errstate(over="ignore"):
        z = calibration.a * np.log(clipped / (1 - clipped)) + calibration.b
    # Stable sigmoid avoids exponential overflow for large finite coefficients.
    result = np.empty_like(z)
    positive = z >= 0
    with np.errstate(under="ignore"):
        result[positive] = 1 / (1 + np.exp(-z[positive]))
        exp_z = np.exp(z[~positive])
        result[~positive] = exp_z / (1 + exp_z)
    return probability_check(result, len(p))

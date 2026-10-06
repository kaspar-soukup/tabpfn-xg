"""Frozen model constructors and offline-testable fit/prediction boundaries.

Optional model packages are imported only by an explicit construction call.
No token handling, acquisition, sampling or cached-file loading lives here.
"""

from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd

from .calibration import Calibration, apply_calibration, positive_probability
from .features import FEATURES


@dataclass(frozen=True)
class CatBoostConfig:
    depth: int = 4
    iterations: int = 200
    learning_rate: float = 0.1
    l2_leaf_reg: int = 10
    random_seed: int = 123
    verbose: bool = False
    allow_writing_files: bool = False
    thread_count: int = 4


@dataclass(frozen=True)
class TabPFNConfig:
    model_path: str = "v3.5_default"
    n_estimators: int = 4
    random_state: int = 123
    thinking_mode: bool = False
    fit_mode: str = "fit_preprocessors"
    inference_precision: str = "auto"


# external_experiment.settings and model_constructor_options in the manifest.
CATBOOST_CONFIG = CatBoostConfig()
TABPFN_CONFIG = TabPFNConfig()


def make_model(name, *, factory=None):
    """Construct an unfitted frozen model; factory injection supports offline tests.

    Explicit TabPFN construction may initialize the optional hosted client.
    This function never calls fit or predict and does not manage credentials.
    """
    if name not in ("catboost", "tabpfn"):
        raise ValueError("Model name must be 'catboost' or 'tabpfn'")
    config = CATBOOST_CONFIG if name == "catboost" else TABPFN_CONFIG
    if factory is None:
        try:
            if name == "catboost":
                from catboost import CatBoostClassifier
                factory = CatBoostClassifier
            else:
                from tabpfn_client import TabPFNClassifier
                factory = TabPFNClassifier
        except ModuleNotFoundError as error:
            package = "catboost" if name == "catboost" else "tabpfn_client"
            if error.name != package:
                raise
            raise ImportError(
                f"Install the optional model dependency with pip install 'tabpfn-xg[{name}]'"
            ) from error
    return factory(**asdict(config))


def _validate_features(x):
    if not isinstance(x, pd.DataFrame) or tuple(x.columns) != FEATURES:
        raise ValueError("Expected a DataFrame with exactly the ordered 50 FEATURES columns")
    try:
        valid = (all(pd.api.types.is_numeric_dtype(dtype) for dtype in x.dtypes)
                 and not np.iscomplexobj(x.to_numpy())
                 and np.isfinite(x.to_numpy(dtype=float)).all())
    except (TypeError, ValueError, OverflowError):
        valid = False
    if not valid:
        raise ValueError("Model features must be finite real numeric values")


def fit_model(model, x, y):
    """Fit explicit context after validation and return the same model.

    Frozen reproduction requires the exact ordered 8,000 historical fit shot IDs
    in the manifest. The caller selects/aligns those rows; this boundary checks
    schema and positional labels, not provenance or sampling. A real hosted
    model may make paid requests here.
    """
    _validate_features(x)
    labels = np.asarray(y)
    if isinstance(y, pd.Series) and not y.index.equals(x.index):
        raise ValueError("Label Series index must match feature row order")
    if (labels.shape != (len(x),) or np.iscomplexobj(labels)
            or not np.isin(labels, [0, 1]).all()):
        raise ValueError("Fit labels must be a one-dimensional vector of 0 and 1 matching feature rows")
    if len(x) == 0 or not np.array_equal(np.unique(labels), [0, 1]):
        raise ValueError("Fit context must contain both binary classes 0 and 1")
    model.fit(x, y)
    return model


def predict_raw(model, x):
    """Validate schema and return uncalibrated class-1 probabilities."""
    _validate_features(x)
    if len(x) == 0:
        return np.empty(0, dtype=float)
    return positive_probability(model, x)


def predict_calibrated(model, x, calibration):
    """Predict raw probabilities then apply the explicitly supplied calibration once.

    Never pass cached calibrated CSV values through this model interface.
    """
    if not isinstance(calibration, Calibration):
        raise ValueError("Supply an explicit Calibration instance")
    return apply_calibration(predict_raw(model, x), calibration)

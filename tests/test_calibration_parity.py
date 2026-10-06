"""Read-only comparison of raw caches with all frozen external predictions."""

import json
import os
from pathlib import Path
import unittest

import numpy as np
import pandas as pd

from tabpfn_xg.calibration import (
    CATBOOST_CALIBRATION, TABPFN_CALIBRATION, apply_calibration, probability_check,
)


@unittest.skipUnless(os.environ.get("TABPFN_RESEARCH_ROOT"),
                     "Set TABPFN_RESEARCH_ROOT to the selected research snapshot")
class CalibrationParityChecks(unittest.TestCase):
    def test_external_raw_caches_reproduce_frozen_predictions(self):
        root = Path(os.environ["TABPFN_RESEARCH_ROOT"])
        frozen = root / "results/xg_external_bundesliga_2023_24"
        expected = pd.read_csv(frozen / "evaluation_predictions.csv")
        selection = json.loads((root / "results/xg_geometry/selection.json").read_text())
        self.assertEqual(len(expected), 908)
        self.assertTrue(expected.id.is_unique)
        for name, config in (("catboost", CATBOOST_CALIBRATION), ("tabpfn", TABPFN_CALIBRATION)):
            with self.subTest(model=name), np.load(frozen / f"{name}.npz", allow_pickle=False) as cache:
                np.testing.assert_array_equal(cache["shot_ids"], expected.id)
                self.assertEqual(selection["geometry_" + name]["calibration"], [config.a, config.b])
                raw = probability_check(cache["p"], len(expected))
                actual = apply_calibration(raw, config)
                np.testing.assert_allclose(actual, expected[name], rtol=0, atol=2e-14)
        probability_check(expected.statsbomb, len(expected))

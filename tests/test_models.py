"""Frozen construction and prediction interfaces without optional packages/calls."""

from dataclasses import asdict, FrozenInstanceError
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import numpy as np
import pandas as pd

from tabpfn_xg.calibration import (
    CATBOOST_CALIBRATION, TABPFN_CALIBRATION, apply_calibration,
)
from tabpfn_xg.features import FEATURES
from tabpfn_xg.models import (
    CATBOOST_CONFIG, TABPFN_CONFIG, fit_model, make_model,
    predict_calibrated, predict_raw,
)


def feature_rows():
    return pd.DataFrame(np.zeros((2, 50)), columns=FEATURES, index=[7, 3])


class ModelChecks(unittest.TestCase):
    def test_frozen_constructor_settings_match_manifest(self):
        manifest = json.loads((Path(__file__).resolve().parents[1]
                               / "provenance/research_manifest.json").read_text())
        settings = manifest["external_experiment"]["settings"]
        options = manifest["model_constructor_options"]
        expected = {
            "catboost": settings["catboost"] | options["catboost"],
            "tabpfn": {k: settings[k] for k in ("model_path", "n_estimators", "thinking_mode")}
                      | options["tabpfn"],
        }
        for name, config in (("catboost", CATBOOST_CONFIG), ("tabpfn", TABPFN_CONFIG)):
            with self.subTest(model=name):
                self.assertEqual(asdict(config), expected[name])
                factory = Mock()
                self.assertIs(make_model(name, factory=factory), factory.return_value)
                factory.assert_called_once_with(**expected[name])
                factory.return_value.fit.assert_not_called()
                factory.return_value.predict_proba.assert_not_called()
                with self.assertRaises(FrozenInstanceError):
                    config.n_estimators = 8

    def test_lazy_optional_constructors_and_actionable_missing_dependency(self):
        for name, package, classifier in (
            ("catboost", "catboost", "CatBoostClassifier"),
            ("tabpfn", "tabpfn_client", "TabPFNClassifier"),
        ):
            factory = Mock()
            with self.subTest(model=name), patch.dict(
                sys.modules, {package: SimpleNamespace(**{classifier: factory})}
            ):
                self.assertIs(make_model(name), factory.return_value)
                factory.assert_called_once()
            with patch.dict(sys.modules, {package: None}):
                with self.assertRaisesRegex(ImportError, rf"tabpfn-xg\[{name}\]"):
                    make_model(name)
        factory = Mock()
        with self.assertRaisesRegex(ValueError, "Model name"):
            make_model("unknown", factory=factory)
        factory.assert_not_called()

    def test_import_and_cached_probability_use_do_not_load_clients(self):
        # Fresh interpreter prevents earlier tests/imports from hiding eager imports.
        code = """
import sys
class BlockClients:
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in ('catboost', 'tabpfn_client'):
            raise AssertionError('Optional client imported during cached use')
sys.meta_path.insert(0, BlockClients())
import tabpfn_xg.models
from tabpfn_xg.calibration import probability_check
assert probability_check([.1, .9], 2).tolist() == [.1, .9]
assert 'catboost' not in sys.modules and 'tabpfn_client' not in sys.modules
"""
        environment = os.environ.copy()
        environment.pop("TABPFN_TOKEN", None)
        completed = subprocess.run([sys.executable, "-c", code], env=environment,
                                   capture_output=True, text=True)
        self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_fit_passes_context_unchanged_and_predictions_map_reversed_classes(self):
        x = feature_rows()
        y = pd.Series([0, 1], index=x.index)
        original = x.copy(deep=True)
        model = Mock(classes_=np.array([1, 0]))
        model.predict_proba.return_value = [[.2, .8], [.7, .3]]
        self.assertIs(fit_model(model, x, y), model)
        self.assertIs(model.fit.call_args.args[0], x)
        self.assertIs(model.fit.call_args.args[1], y)
        np.testing.assert_array_equal(predict_raw(model, x), [.2, .7])
        self.assertIs(model.predict_proba.call_args.args[0], x)
        for config in (CATBOOST_CALIBRATION, TABPFN_CALIBRATION):
            np.testing.assert_array_equal(predict_calibrated(model, x, config),
                                          apply_calibration([.2, .7], config))
        pd.testing.assert_frame_equal(x, original)

    def test_bad_features_fail_before_fit_or_prediction(self):
        x = feature_rows()
        invalid = [x.to_numpy(), x.iloc[:, ::-1], x.iloc[:, :-1],
                   x.assign(outcome=[0, 1])]
        duplicate = x.copy()
        duplicate.columns = [FEATURES[0]] * 50
        invalid.append(duplicate)
        for value in (np.nan, np.inf, "bad", "0.5", 1j):
            bad = x.astype(object)
            bad.iloc[0, 0] = value
            invalid.append(bad)
        for bad in invalid:
            with self.subTest(columns=getattr(bad, "columns", None)):
                model = Mock()
                with self.assertRaises(ValueError):
                    fit_model(model, bad, [0, 1])
                with self.assertRaises(ValueError):
                    predict_raw(model, bad)
                model.fit.assert_not_called()
                model.predict_proba.assert_not_called()

    def test_bad_labels_fail_before_fit(self):
        x = feature_rows()
        invalid = ([0], [[0], [1]], [0, 2], [0, np.nan], [0, 0],
                   [1, 1], [0j, 1j], ["0", "1"],
                   pd.Series([0, 1], index=x.index[::-1]))
        model = Mock()
        for y in invalid:
            with self.subTest(y=y), self.assertRaises(ValueError):
                fit_model(model, x, y)
        with self.assertRaisesRegex(ValueError, "both binary classes"):
            fit_model(model, x.iloc[:0], [])
        model.fit.assert_not_called()

    def test_empty_prediction_and_invalid_calibration_do_not_call_model(self):
        model = Mock()
        x = feature_rows().iloc[:0]
        self.assertEqual(predict_raw(model, x).shape, (0,))
        self.assertEqual(predict_calibrated(model, x, TABPFN_CALIBRATION).shape, (0,))
        with self.assertRaisesRegex(ValueError, "Calibration instance"):
            predict_calibrated(model, feature_rows(), None)
        model.predict_proba.assert_not_called()

    def test_service_errors_and_invalid_probabilities_are_not_hidden(self):
        model = Mock(classes_=np.array([0, 1]))
        model.predict_proba.side_effect = RuntimeError("fake service unavailable")
        with self.assertRaisesRegex(RuntimeError, "fake service unavailable"):
            predict_raw(model, feature_rows())
        model.predict_proba.side_effect = None
        model.predict_proba.return_value = [[.2, .9], [.5, .5]]
        with self.assertRaisesRegex(ValueError, "sum to 1"):
            predict_calibrated(model, feature_rows(), TABPFN_CALIBRATION)

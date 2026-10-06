"""Offline probability and frozen-calibration boundaries; no model dependencies."""

from dataclasses import FrozenInstanceError
import json
from pathlib import Path
import unittest

import numpy as np

from tabpfn_xg.calibration import (
    CATBOOST_CALIBRATION, TABPFN_CALIBRATION, Calibration,
    apply_calibration, positive_probability, probability_check,
)


class FakeModel:
    def __init__(self, classes, probabilities):
        self.classes_ = classes
        self.probabilities = probabilities

    def predict_proba(self, x):
        return self.probabilities


class ProbabilityChecks(unittest.TestCase):
    def test_positive_class_mapping(self):
        for classes, matrix in (([1, 0], [[.2, .8], [.7, .3]]),
                                ([0, 1], [[.8, .2], [.3, .7]])):
            with self.subTest(classes=classes):
                np.testing.assert_array_equal(
                    positive_probability(FakeModel(classes, matrix), [0, 0]), [.2, .7])

    def test_invalid_class_labels_and_counts(self):
        for classes in ([1, 1], [0, 0], [1], [0, 1, 1], [0, 2],
                        ["0", "1"], [[0, 1]], [0, np.nan]):
            with self.subTest(classes=classes), self.assertRaisesRegex(ValueError, "classes"):
                positive_probability(FakeModel(classes, [[.2, .8]]), [0])

    def test_invalid_probability_matrices(self):
        for matrix in ([.2, .8], [[.2, .8], [.3, .7]], [[.2, .7]],
                       [[np.nan, .8]], [[np.inf, .8]], [[-.1, 1.1]],
                       [[1.1, -.1]], [["bad", .8]]):
            with self.subTest(matrix=matrix), self.assertRaises(ValueError):
                positive_probability(FakeModel([0, 1], matrix), [0])

    def test_row_sum_tolerance_and_empty_batch(self):
        np.testing.assert_array_equal(
            positive_probability(FakeModel([0, 1], [[.2, .800001]]), [0]), [.800001])
        self.assertEqual(positive_probability(FakeModel([0, 1], np.empty((0, 2))), []).shape, (0,))

    def test_probability_vector_boundaries(self):
        np.testing.assert_array_equal(probability_check([0, .5, 1], 3), [0, .5, 1])
        self.assertEqual(probability_check([], 0).shape, (0,))
        for p in (0.5, [[.5]], [.1, .2], [np.nan], [np.inf], [-1e-12],
                  [1 + 1e-12], ["bad"], [complex(.5, .1)], np.array([.5 + .1j])):
            with self.subTest(p=p), self.assertRaises(ValueError):
                probability_check(p, 1)
        for n in (-1, 1.0, True, "1"):
            with self.subTest(n=n), self.assertRaisesRegex(ValueError, "row count"):
                probability_check([.5], n)


class CalibrationChecks(unittest.TestCase):
    def test_frozen_parameters_match_portable_manifest(self):
        manifest = json.loads((Path(__file__).resolve().parents[1] /
                               "provenance/research_manifest.json").read_text())
        # Locate the external freeze without relying on a local research path.
        selection = manifest["external_experiment"]["frozen_selection"]
        for name, config in (("catboost", CATBOOST_CALIBRATION), ("tabpfn", TABPFN_CALIBRATION)):
            choice = selection["geometry_" + name]
            self.assertEqual(choice["variant"], "calibrated")
            self.assertEqual([config.a, config.b], choice["calibration"])
            self.assertEqual(config.clip, 1e-7)

    def test_known_distortion_and_identity(self):
        # Source recovery test's distortion [1.5, -.4], with analytic anchors.
        p = np.array([.2, .5, .8])
        config = Calibration(1.5, -.4)
        expected = np.array([1 / (1 + 8 * np.exp(.4)),
                             1 / (1 + np.exp(.4)), 1 / (1 + np.exp(.4) / 8)])
        np.testing.assert_allclose(apply_calibration(p, config), expected, rtol=0, atol=2e-16)
        np.testing.assert_allclose(apply_calibration(p, Calibration(1, 0)), p, rtol=0, atol=2e-16)
        np.testing.assert_array_equal(p, [.2, .5, .8])

    def test_clipping_monotonicity_and_empty_input(self):
        for config in (CATBOOST_CALIBRATION, TABPFN_CALIBRATION):
            p = np.array([0, 1e-9, 1e-7, .1, .5, .9, 1 - 1e-7, 1])
            calibrated = apply_calibration(p, config)
            self.assertTrue(np.all(np.diff(calibrated) >= 0))
            self.assertTrue(np.all((calibrated > 0) & (calibrated < 1)))
            np.testing.assert_array_equal(calibrated[:3], np.repeat(calibrated[0], 3))
            self.assertEqual(calibrated[-1], calibrated[-2])
            self.assertEqual(apply_calibration([], config).shape, (0,))

    def test_invalid_calibration_inputs_and_configuration(self):
        for p in (0.5, [[.5]], [np.nan], [-.1], [1.1], ["bad"]):
            with self.subTest(p=p), self.assertRaises(ValueError):
                apply_calibration(p, TABPFN_CALIBRATION)
        with self.assertRaisesRegex(ValueError, "Calibration instance"):
            apply_calibration([.5], [1, 0])
        for params in ((0, 0), (-1, 0), (np.nan, 0), (1, np.inf),
                       (1, 0, 0), (1, 0, .5), (1, 0, np.nan), ("bad", 0),
                       ([1], [0], [1e-7])):
            with self.subTest(params=params), self.assertRaises(ValueError):
                Calibration(*params)
        with self.assertRaises(FrozenInstanceError):
            TABPFN_CALIBRATION.a = 2

    def test_stable_sigmoid_for_large_coefficients(self):
        with np.errstate(all="raise"):
            np.testing.assert_array_equal(
                apply_calibration([0, .5, 1], Calibration(1e308, 0)), [0, .5, 1])

"""Offline protocol tests and optional read-only frozen-result parity."""

import json
import os
from pathlib import Path
import unittest

import numpy as np
import pandas as pd

from tabpfn_xg.evaluation import sample_rows, metrics, clustered_difference


class EvaluationChecks(unittest.TestCase):
    def test_nested_reproducible_sampling(self):
        y = np.tile([0] * 9 + [1], 1200)
        rows = np.arange(len(y))
        a = sample_rows(rows, y, 123, 2000)
        b = sample_rows(rows, y, 123, 8000)
        self.assertTrue(set(a) <= set(b))
        self.assertEqual(y[a].sum(), 200)
        self.assertEqual(y[b].sum(), 800)
        np.testing.assert_array_equal(b, sample_rows(rows, y, 123, 8000))
        self.assertFalse(np.array_equal(b, sample_rows(rows, y, 456, 8000)))

    def test_sampling_pool_rounding_and_limits(self):
        y = [0, 1, 0, 1, 0, 0]
        rows = np.array([1, 2, 4, 5])
        a = sample_rows(rows, y, 123, 2)
        self.assertTrue(set(a) <= set(rows))
        self.assertEqual(np.asarray(y)[a].sum(), 0)  # Python ties-to-even rounding.
        self.assertEqual(len(sample_rows(rows, y, 123, 0)), 0)
        self.assertEqual(set(sample_rows(rows, y, 123, 4)), set(rows))
        for bad_rows, size in (([1, 1], 1), ([-1], 1), ([6], 1), ([1.0], 1),
                               ([], 0), (rows, 5), (rows, -1), (rows, True)):
            with self.subTest(rows=bad_rows, size=size), self.assertRaises(ValueError):
                sample_rows(bad_rows, y, 123, size)

    def test_metrics_analytic_and_tied_auc(self):
        result = metrics([0, 1, 0, 1], [.25, .75, .5, .5])
        self.assertAlmostEqual(result['log_loss'], -(np.log(.75) + np.log(.5)) / 2)
        self.assertAlmostEqual(result['brier'], .15625)
        self.assertEqual(result['auc'], .875)
        self.assertEqual(result['predicted_rate'], .5)
        self.assertEqual(result['observed_rate'], .5)
        self.assertEqual((result['shots'], result['goals']), (4, 2))
        self.assertEqual(metrics([0, 1], [1, 0])['auc'], 0)

    def test_endpoints_and_single_class(self):
        result = metrics([0, 1], [1, 0])
        self.assertAlmostEqual(result['log_loss'], -np.log(np.finfo(float).eps))
        self.assertEqual(result['brier'], 1)
        self.assertTrue(np.isnan(metrics([0], [0])['auc']))

    def test_identical_paired_models(self):
        p = [.1, .8, .2, .4, .6]
        result = clustered_difference([0, 1, 0, 0, 1], p, p, [1, 1, 2, 2, 3])
        for value in result.values():
            self.assertEqual(value, dict(difference=0, ci95=[0, 0]))

    def test_whole_unequal_matches_and_direction(self):
        args = (np.zeros(4), [.1, .1, .1, .5], [.2, .2, .2, .1], [1, 1, 1, 2])
        result = clustered_difference(*args)
        self.assertAlmostEqual(result['brier']['difference'], .0375)
        np.testing.assert_allclose(result['brier']['ci95'], [-.03, .24])
        self.assertEqual(result, clustered_difference(*args))
        reverse = clustered_difference(args[0], args[2], args[1], args[3])
        for metric, value in result.items():
            self.assertAlmostEqual(reverse[metric]['difference'], -value['difference'])
            np.testing.assert_allclose(reverse[metric]['ci95'], -np.array(value['ci95'])[::-1])

    def test_bootstrap_endpoint_clipping_and_single_match(self):
        result = clustered_difference([0, 1], [1, 0], [0, 1], ['a', 'a'])
        self.assertAlmostEqual(result['brier']['difference'], 1 - 2e-15, places=16)
        for value in result.values():
            np.testing.assert_array_equal(value['ci95'], [value['difference']] * 2)

    def test_rejected_evaluation_inputs(self):
        for y, p in (([], []), ([2], [.5]), ([[0]], [.5]), ([np.nan], [.5]),
                     ([0], [np.inf]), ([0], [-.1]), ([0], [.1, .2])):
            with self.subTest(y=y, p=p), self.assertRaises(ValueError):
                metrics(y, p)
        for groups in ([1], [1, None], [1, np.inf], [[1, 2]]):
            with self.subTest(groups=groups), self.assertRaises(ValueError):
                clustered_difference([0, 1], [.1, .9], [.2, .8], groups)
        for config in ({'replicates': 0}, {'replicates': 1.5}, {'seed': -1}):
            with self.subTest(config=config), self.assertRaises(ValueError):
                clustered_difference([0, 1], [.1, .9], [.2, .8], [1, 2], **config)


@unittest.skipUnless(os.environ.get('TABPFN_RESEARCH_ROOT'), 'Set TABPFN_RESEARCH_ROOT for parity')
class EvaluationParityChecks(unittest.TestCase):
    def test_frozen_metrics_and_intervals(self):
        root = Path(os.environ['TABPFN_RESEARCH_ROOT']) / 'results/xg_external_bundesliga_2023_24'
        predictions = pd.read_csv(root / 'evaluation_predictions.csv')
        expected = pd.read_csv(root / 'evaluation_metrics.csv')
        self.assertEqual(len(predictions), 908)
        self.assertEqual(predictions.match_id.nunique(), 34)
        for row in expected.to_dict('records'):
            actual = metrics(predictions.outcome, predictions[row.pop('model')])
            for key, value in row.items():
                np.testing.assert_allclose(actual[key], value, rtol=0, atol=2e-14)
        differences = json.loads((root / 'paired_differences.json').read_text())
        for other, expected in differences.items():
            actual = clustered_difference(predictions.outcome, predictions.tabpfn,
                                          predictions[other], predictions.match_id)
            for metric, values in expected.items():
                for key, value in values.items():
                    np.testing.assert_allclose(actual[metric][key], value, rtol=0, atol=2e-14)

    def test_exact_frozen_fit_sample(self):
        root = Path(os.environ['TABPFN_RESEARCH_ROOT'])
        full = pd.read_pickle(root / 'data/processed/football_processed.pickle')
        splits = pd.read_csv(root / 'results/xg_pilot/splits.csv')
        np.testing.assert_array_equal(full.id, splits.shot_id)
        rows = splits.loc[splits.role == 'fit', 'position'].to_numpy()
        sample = sample_rows(rows, full.shot_outcome_encoded, 123, 8000)
        manifest = json.loads((Path(__file__).resolve().parents[1] /
                               'provenance/research_manifest.json').read_text())
        self.assertEqual(full.iloc[sample].id.tolist(), manifest['external_experiment']['fit_shot_ids'])
        roles = ['fit', 'calibration', 'validation', 'evaluation']
        for i, role in enumerate(roles):
            matches = set(splits.loc[splits.role == role, 'match_id'])
            for other in roles[i + 1:]:
                self.assertTrue(matches.isdisjoint(splits.loc[splits.role == other, 'match_id']))

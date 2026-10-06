"""Read-only full asset preparation against the explicitly selected research snapshot."""

import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import numpy as np
import pandas as pd

from tabpfn_xg.assets import prepare_external
from tabpfn_xg.features import FEATURES


@unittest.skipUnless(os.environ.get('TABPFN_RESEARCH_ROOT'),
                     'Set TABPFN_RESEARCH_ROOT to the selected research snapshot')
class AssetParityChecks(unittest.TestCase):
    def test_complete_external_dataset_matches_frozen_rows_and_features(self):
        root = Path(os.environ['TABPFN_RESEARCH_ROOT'])
        assets = Path(__file__).resolve().parents[1] / 'assets/external'
        source = json.loads((assets / 'source_manifest.json').read_text())
        frozen = root / 'results/xg_external_bundesliga_2023_24'
        predictions = pd.read_csv(frozen / 'evaluation_predictions.csv', float_precision='round_trip')
        with TemporaryDirectory() as directory:
            output = Path(directory) / 'external'
            prepare_external(root / 'data/external/bundesliga_2023_24', assets / 'model_predictions.csv',
                             output, source, offline=True)
            records = json.loads((output / 'shots.json').read_text())
        actual = pd.DataFrame(records)
        self.assertEqual(len(actual), 908)
        self.assertEqual(actual.match_id.nunique(), 34)
        self.assertEqual(actual.outcome.sum(), 102)
        self.assertTrue(actual.id.is_unique)
        for name in predictions:
            np.testing.assert_array_equal(actual[name], predictions[name])
        features = pd.read_csv(frozen / 'features.csv')
        np.testing.assert_allclose(actual[list(FEATURES)], features, atol=2e-14, rtol=0)
